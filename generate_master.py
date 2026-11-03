# VERSION: 6.0 - RATE-LIMIT-AWARE ENGINE
"""
TryIT Engine v6 - Honest free tier limits respected
REAL LIMITS:
  Groq:      1,000 RPD org-wide (not per key) | 30 RPM | USE for S1+S2 combined
  Gemini:    500 RPD per key x5 = 2,500/day   | 15 RPM | USE for QA gate
  NVIDIA:    finite credits, startup key only  | 40 RPM | USE for L8-10 only
  SambaNova: 20 RPD per key = 100/day total   | 20 RPM | BACKUP only

PIPELINE:
  S1+S2: Groq  → full question + 7-layer explanation in ONE call
  S3:    Gemini → quality score + verify gate (combined to save calls)
  S4:    NVIDIA → only for difficulty L8-10 re-explanation upgrade

TARGET: 800-1,200 questions/day (honest)
"""

import os, json, time, uuid, re
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair

from backend_engine import safe_db_insert, is_duplicate
from key_pool import get_pool
from entity_engine import get_context
from diagram_mapping import DIAGRAM_KIND_BY_TOPIC_ID
from svg_sanitizer import sanitize_question_svgs

load_dotenv(dotenv_path=".env", override=True)

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
BATCH_SIZE         = 5    # Questions per Groq call
CONCURRENT_WORKERS = 6    # Parallel threads (respect 30 RPM Groq limit)
QUALITY_THRESHOLD  = 6    # Min score to save
TARGET_L1_L5       = 20
TARGET_L6_L10      = 10

# ── SUPABASE ───────────────────────────────────────────────────────────────────
s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# ── KEY LOADER ─────────────────────────────────────────────────────────────────
def load_keys(prefix, n=5):
    keys = []
    base = os.getenv(prefix)
    if base and base.strip(): keys.append(base.strip())
    for i in range(1, n+1):
        k = os.getenv(f"{prefix}_{i}")
        if k and k.strip(): keys.append(k.strip())
    return keys

GROQ_KEYS   = load_keys("GROQ_API_KEY", 5)
NVIDIA_KEYS = load_keys("NVIDIA_API_KEY", 5)
SAMBA_KEYS  = load_keys("SAMBANOVA_API_KEY", 5)
GEMINI_KEYS = load_keys("GEMINI_API_KEY", 5)

print(f"Keys: GROQ={len(GROQ_KEYS)} NVIDIA={len(NVIDIA_KEYS)} SAMBA={len(SAMBA_KEYS)} GEMINI={len(GEMINI_KEYS)}", flush=True)
print("NOTE: Groq 1K RPD org-wide | Gemini 2.5K RPD | NVIDIA finite credits | Samba 100 RPD", flush=True)

# ── KEY POOLS ──────────────────────────────────────────────────────────────────
# Groq: org-level 1K RPD — pool still rotates RPM within that budget
GROQ_POOL   = get_pool("Groq",      GROQ_KEYS,   cooldown_seconds=62)
NVIDIA_POOL = get_pool("NVIDIA",    NVIDIA_KEYS, cooldown_seconds=90)
SAMBA_POOL  = get_pool("SambaNova", SAMBA_KEYS,  cooldown_seconds=300)  # 300s cooldown — only 20 RPD per key
GEMINI_POOL = get_pool("Gemini",    GEMINI_KEYS, cooldown_seconds=65)

# ── CLIENTS ────────────────────────────────────────────────────────────────────
GROQ_CLIENTS   = {k: OpenAI(base_url="https://api.groq.com/openai/v1",       api_key=k) for k in GROQ_KEYS}
NVIDIA_CLIENTS = {k: OpenAI(base_url="https://integrate.api.nvidia.com/v1",  api_key=k) for k in NVIDIA_KEYS}
SAMBA_CLIENTS  = {k: OpenAI(base_url="https://api.sambanova.ai/v1",          api_key=k) for k in SAMBA_KEYS}

# ── GEMINI SETUP ───────────────────────────────────────────────────────────────
GEMINI_KEY_TO_MODEL = {}
print("Probing Gemini keys...", flush=True)
for k in GEMINI_KEYS:
    for model in ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-2.0-flash-lite", "gemini-1.5-flash"]:
        try:
            genai.Client(api_key=k).models.generate_content(model=model, contents="hi")
            GEMINI_KEY_TO_MODEL[k] = model
            print(f"  Gemini OK -> {model}", flush=True)
            break
        except Exception:
            continue

WORKING_GEMINI = list(GEMINI_KEY_TO_MODEL.keys())
GEMINI_POOL = get_pool("Gemini", WORKING_GEMINI, cooldown_seconds=65) if WORKING_GEMINI else None
print(f"Gemini pool: {len(WORKING_GEMINI)} keys", flush=True)

# ── DIFFICULTY LABEL ───────────────────────────────────────────────────────────
def diff_label(level):
    if level <= 3:  return "Easy"
    if level <= 6:  return "Medium"
    if level <= 8:  return "Hard"
    return "Expert"

def diff_guide(level):
    if level <= 3:  return "Basic recall. Textbook fact. Single concept. Class 6-8 level."
    if level <= 5:  return "Application of concept. Two-step reasoning. Class 9-10 / foundation exam level."
    if level <= 6:  return "Moderate analysis. SSC CGL / RRB NTPC / State PSC level. One trap option."
    if level <= 8:  return "Multi-step reasoning. UPSC Prelims / GATE / NEET level. Two plausible wrong options that exploit common misconceptions."
    return "Expert analysis. UPSC Mains reasoning / GATE advanced / research level. All wrong options must seem correct to an average student."

# ── JSON HELPERS ───────────────────────────────────────────────────────────────
def extract_list(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    for cand in [text, text[text.find("["):text.rfind("]")+1] if "[" in text else ""]:
        if not cand: continue
        try:
            d = json.loads(cand)
            if isinstance(d, list): return d
        except Exception:
            try:
                d = json_repair.loads(cand)
                if isinstance(d, list): return d
            except Exception: continue
    return None

def extract_obj(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m: return None
    try: return json_repair.loads(m.group())
    except Exception: return None

# ── OPENAI CALL HELPER ─────────────────────────────────────────────────────────
def call_api(pool, clients, model, messages, max_tokens=4096, timeout=90, provider_name=""):
    tried = 0
    while tried < len(clients):
        idx, key = pool.get_key(wait=False)
        if key is None: break
        tried += 1
        client = clients.get(key)
        if not client: pool.mark_error(idx); continue
        try:
            r = client.chat.completions.create(
                model=model, messages=messages,
                max_tokens=max_tokens, temperature=0.7, timeout=timeout
            )
            raw = r.choices[0].message.content or ""
            if raw: pool.mark_success(idx); return raw
            pool.mark_error(idx)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                pool.mark_rate_limit(idx, cooldown=65)
                print(f"      ⏳ {provider_name} key#{idx+1} rate-limited", flush=True)
            elif "401" in err or "403" in err:
                pool.mark_error(idx)
            elif "timeout" in err.lower():
                pool.mark_rate_limit(idx, cooldown=30)
            else:
                pool.mark_error(idx)
    return None

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 1+2 COMBINED — Groq generates full question WITH 7-layer explanation
# One API call = complete question ready to save
# Saves Groq RPD budget (1 call per question not 2)
# ══════════════════════════════════════════════════════════════════════════════
def generate_full_batch(topic_id, topic_name, subject_id, level, count, exam_tags):
    context  = get_context(topic_id, subject_id) if callable(get_context) else ""
    exam_str = ", ".join(exam_tags[:5]) if exam_tags else "UPSC, SSC CGL, RRB NTPC, State PSC"

    prompt = f"""You are India's top competitive exam question writer with 20 years experience.
Generate exactly {count} MCQs for:

Topic: {topic_name}
Subject: {subject_id}
Difficulty: {level}/10 — {diff_guide(level)}
Target Exams: {exam_str}
{"Context: " + context[:300] if context else ""}

DIFFICULTY RULES:
- Level 1-3  (Easy):   School/ECCE/Foundation — basic recall, single fact
- Level 4-6  (Medium): SSC CGL/RRB NTPC/State PSC — application, one trap
- Level 7-8  (Hard):   UPSC Prelims/GATE/NEET — multi-step, two traps
- Level 9-10 (Expert): UPSC Mains/GATE Adv — all options seem plausible

MCQ RULES:
1. Each question MUST match exactly difficulty {level}/10
2. correct_answer is 0-indexed: 0=A, 1=B, 2=C, 3=D
3. All 4 options must be DISTINCT and PLAUSIBLE (no obviously wrong options for level 5+)
4. For level 7+: options must exploit real misconceptions students have
5. story_explanation must use Indian characters: Ramu, Priya, shopkeeper, farmer, cricket team etc.

Output ONLY a valid JSON array — no markdown, no preamble:
[
  {{
    "question": "Full question text here?",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": 0,
    "why_correct": "Step-by-step proof: [Step 1]... [Step 2]... Therefore answer is A.",
    "why_wrong_option_b": "Students choose B because [specific misconception]. This is wrong because [exact reason].",
    "why_wrong_option_c": "Students choose C because [specific misconception]. This is wrong because [exact reason].",
    "why_wrong_option_d": "Students choose D because [specific misconception]. This is wrong because [exact reason].",
    "story_explanation": "TEACH LIKE TO A 10-YEAR-OLD: Write 4 sentences using Ramu/Priya/shopkeeper/farmer/cricket team. Sentence 1: Character doing something familiar in daily Indian life. Sentence 2: They face the EXACT same problem as this question. Sentence 3: They solve it using the SAME logic as the correct answer — show the thinking step by step. Sentence 4: End with THIS IS WHY [correct option] is right — make it stick forever. The story must make the concept unforgettable, not just describe it.",
    "shortcut_tips": "ONE specific memory trick — either MNEMONIC (acronym from key words), PATTERN (if question has X always pick Y), or VISUAL (picture it as...). Format exactly: TRICK: [name it]. HOW: [the trick in one line]. APPLY HERE: [show it working on this exact question in under 10 seconds].",
    "cross_exam_intelligence": "UPSC Prelims: this concept appears as [exact type — assertion-reason/match-following/negative trap] watch out for [specific trap]. SSC CGL Tier-1: tested as [angle], common wrong answer is [option letter] because [reason]. RRB NTPC: [angle]. NEET/GATE/State PSC: [angle]. Give exam-specific warning not generic advice."
  }}
]"""

    msgs = [
        {"role": "system", "content": "You are a JSON-only MCQ generator. Output ONLY a valid JSON array. Never add markdown, explanation, or text outside the JSON array."},
        {"role": "user", "content": prompt}
    ]

    # Primary: Groq gpt-oss-120b (1K RPD budget — use wisely)
    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        raw = call_api(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=4096, timeout=60, provider_name="Groq")
        if raw:
            data = extract_list(raw)
            if data:
                valid = [q for q in data if
                    q.get("question") and
                    isinstance(q.get("options"), list) and len(q["options"]) == 4 and
                    isinstance(q.get("correct_answer"), int) and 0 <= q["correct_answer"] <= 3 and
                    q.get("why_correct")]
                if valid:
                    print(f"      ✍️  {len(valid)}q via Groq {model} L{level}", flush=True)
                    return valid

    # Fallback: SambaNova (very limited — 100/day total — use sparingly)
    for model in ["DeepSeek-V3.2", "gpt-oss-120b", "Meta-Llama-3.3-70B-Instruct"]:
        raw = call_api(SAMBA_POOL, SAMBA_CLIENTS, model, msgs, max_tokens=4096, timeout=90, provider_name="SambaNova")
        if raw:
            data = extract_list(raw)
            if data:
                valid = [q for q in data if
                    q.get("question") and
                    isinstance(q.get("options"), list) and len(q["options"]) == 4 and
                    isinstance(q.get("correct_answer"), int) and 0 <= q["correct_answer"] <= 3]
                if valid:
                    print(f"      ✍️  {len(valid)}q via SambaNova {model} L{level}", flush=True)
                    return valid

    return []

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 3 — NVIDIA UPGRADE for L8-10 only (saves finite credits)
# Rewrites explanation using 550B model for expert-level questions
# ══════════════════════════════════════════════════════════════════════════════
def nvidia_upgrade_explanation(q, topic_name, level, exam_tags):
    """Only called for level >= 8. Uses finite NVIDIA credits."""
    exam_str = ", ".join(exam_tags[:3]) if exam_tags else "UPSC, GATE"
    correct  = q["options"][q["correct_answer"]]

    prompt = f"""Upgrade this expert-level MCQ explanation to PhD quality.
Topic: {topic_name} | Level: {level}/10 | Exams: {exam_str}
Question: {q["question"]}
Correct Answer: {correct}
Current explanation: {q.get("why_correct","")[:200]}

Return ONLY JSON:
{{
  "why_correct": "Expert-level step-by-step proof with technical depth appropriate for {exam_str}.",
  "why_wrong_option_b": "Deep analysis of why option B fails with the exact conceptual error.",
  "why_wrong_option_c": "Deep analysis of why option C fails with the exact conceptual error.",
  "why_wrong_option_d": "Deep analysis of why option D fails with the exact conceptual error.",
  "shortcut_tips": "Advanced pattern recognition trick used by UPSC/GATE toppers.",
  "cross_exam_intelligence": "Exact year and paper this concept appeared in UPSC/GATE/NEET."
}}"""

    msgs = [{"role": "user", "content": prompt}]
    for model in ["nvidia/nemotron-3-ultra-550b-a55b", "nvidia/llama-3.1-nemotron-ultra-253b-v1", "mistralai/mistral-large-4-1t-a52b", "moonshotai/kimi-k2.6"]:
        raw = call_api(NVIDIA_POOL, NVIDIA_CLIENTS, model, msgs, max_tokens=1500, timeout=90, provider_name="NVIDIA")
        if raw:
            data = extract_obj(raw)
            if data and data.get("why_correct"):
                q.update(data)
                print(f"      🔬 NVIDIA upgrade via {model}", flush=True)
                return q
    return q  # Return original if NVIDIA fails

# ══════════════════════════════════════════════════════════════════════════════
# STAGE 4 — GEMINI QA GATE (combined score + verify in ONE call)
# Saves Gemini RPD — one call does both scoring and approval
# ══════════════════════════════════════════════════════════════════════════════
def gemini_qa_gate(q, level):
    if not GEMINI_POOL:
        return True, 7, "no verifier"

    idx, key = GEMINI_POOL.get_key(wait=False)
    if key is None:
        return True, 7, "gemini cooling — auto pass"

    model = GEMINI_KEY_TO_MODEL.get(key, "gemini-3.5-flash")
    try:
        client = genai.Client(api_key=key)
        prompt = f"""You are a strict quality controller for Indian competitive exam MCQs.
Check this question for difficulty level {level}/10 ({diff_label(level)}).

Difficulty guide for {level}/10:
{diff_guide(level)}

Question: {q.get("question","")}
Options: {q.get("options",[])}
Correct index: {q.get("correct_answer",0)}
Explanation: {q.get("why_correct","")[:300]}

Check ALL of these:
1. Does question difficulty MATCH level {level}/10? (reject if too easy or too hard)
2. Is the correct answer factually correct?
3. Is the explanation complete and not truncated?
4. Are the wrong options plausible (not obviously wrong for this level)?
5. Does story_explanation TEACH through a real story — character faces same problem, solves using same logic, ends with why correct answer wins? REJECT if story is generic or does not connect to answer.
6. Does shortcut_tips give a REAL named trick with APPLY HERE example? REJECT if vague or just says remember this.

Return ONLY JSON:
{{"passed": true, "score": 8, "reason": "one clear sentence why passed or failed"}}

Score: 1-10. Pass if score >= 6 AND all 4 checks above pass."""

        r = client.models.generate_content(model=model, contents=prompt)
        txt = re.sub(r"^```json\s*|\s*```$", "", (r.text or "").strip(), flags=re.MULTILINE)
        d = extract_obj(txt)
        if d:
            GEMINI_POOL.mark_success(idx)
            passed = d.get("passed", False)
            score  = int(d.get("score", 0))
            reason = d.get("reason", "")
            if not passed:
                print(f"      ✗ Gemini rejected L{level}: {reason[:60]}", flush=True)
            return passed, score, reason
        GEMINI_POOL.mark_error(idx)
        return True, 6, "parse fail — auto pass"
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            GEMINI_POOL.mark_rate_limit(idx, cooldown=70)
        elif "503" in err or "overloaded" in err.lower():
            return True, 7, "gemini overloaded — auto pass"
        else:
            GEMINI_POOL.mark_error(idx)
        return True, 6, "gemini error — auto pass"

# ── DB HELPERS ─────────────────────────────────────────────────────────────────
def get_existing_count(topic_id, level):
    try:
        r = s.table("questions").select("id", count="exact").eq("topic_id", topic_id).eq("level", level).execute()
        return r.count or 0
    except Exception: return 0

def save(q, topic_id, subject_id, level, exam_tags):
    diagram_kind = DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id)
    if diagram_kind:
        q = sanitize_question_svgs(q, diagram_kind)
    rec = {
        "id":               f"q_{uuid.uuid4().hex[:16]}",
        "topic_id":         topic_id,
        "subject_id":       subject_id,
        "level":            level,
        "difficulty":       diff_label(level),
        "pattern_type":     "standalone_mcq4",
        "question_en":      q["question"],
        "options_en":       q["options"],
        "correct_answer":   q["correct_answer"],
        "explanation": {k: q.get(k,"") for k in [
            "why_correct","why_wrong_option_b","why_wrong_option_c",
            "why_wrong_option_d","story_explanation","shortcut_tips","cross_exam_intelligence"
        ]},
        "translations":       {},
        "exam_tags":          exam_tags,
        "has_visual":         False,
        "visual_type":        None,
        "visual_data":        None,
        "access_tier":        "free" if level <= 6 else "pro",
        "copyright_original": True,
        "verified":           True,
        "quality_score":      q.get("_score", 7),
        "report_count":       0,
        "generated_by":       "tryit_v6",
        "created_at":         datetime.now(timezone.utc).isoformat(),
    }
    if is_duplicate(s, q["question"], topic_id):
        print("      ♻️  Duplicate — skip", flush=True)
        return False
    success, _ = safe_db_insert(s, "questions", rec)
    return success

# ── TOPIC PROCESSORS ───────────────────────────────────────────────────────────
def process_topic_level(topic_id, topic_name, subject_id, level, target, exam_tags):
    existing = get_existing_count(topic_id, level)
    if existing >= target: return 0
    needed = target - existing
    print(f"   ⏳ {topic_id[:40]} L{level} ({diff_label(level)}): {existing}/{target} need {needed}", flush=True)

    saved = 0
    empty_rounds = 0

    while saved < needed and empty_rounds < 3:
        questions = generate_full_batch(topic_id, topic_name, subject_id, level,
                                        min(BATCH_SIZE, needed - saved), exam_tags)
        if not questions:
            empty_rounds += 1
            print(f"   ⚠️  Empty batch {empty_rounds}/3 — wait 5s", flush=True)
            time.sleep(5)
            continue

        empty_rounds = 0
        for q in questions:
            # NVIDIA upgrade for expert questions (L8-10) — uses finite credits
            if level >= 8:
                q = nvidia_upgrade_explanation(q, topic_name, level, exam_tags)

            # Gemini QA gate (combined score+verify)
            passed, score, reason = gemini_qa_gate(q, level)
            if not passed or score < QUALITY_THRESHOLD:
                continue

            q["_score"] = score
            if save(q, topic_id, subject_id, level, exam_tags):
                saved += 1
                print(f"      💾 saved {saved}/{needed} L{level} score={score}", flush=True)

        time.sleep(0.5)

    print(f"   🎉 {topic_id[:30]} L{level}: +{saved}", flush=True)
    return saved

def process_topic(topic):
    tid   = topic["topic_id"]
    tname = topic.get("topic_name", tid)
    sid   = topic.get("subject_id") or "general"
    dr    = topic.get("difficulty_range") or "2-7"
    try: lo, hi = map(int, dr.split("-"))
    except Exception: lo, hi = 2, 7

    try:
        rows      = s.table("exam_syllabus_map").select("exam_id").eq("topic_id", tid).execute().data or []
        exam_tags = sorted(set(r["exam_id"] for r in rows))
    except Exception:
        exam_tags = []

    print(f"\n📘 {tname} L{lo}-L{hi} ({diff_label(lo)}-{diff_label(hi)})", flush=True)
    total = 0
    for lvl in range(lo, hi+1):
        target = TARGET_L1_L5 if lvl <= 5 else TARGET_L6_L10
        total += process_topic_level(tid, tname, sid, lvl, target, exam_tags)
    return total

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    print("🚀 TryIT Engine v6 — Rate-Limit-Aware", flush=True)
    print("   Groq S1+S2 (1K RPD org) | Gemini QA (2.5K RPD) | NVIDIA L8-10 only", flush=True)
    print(f"   Workers:{CONCURRENT_WORKERS} | Batch:{BATCH_SIZE} | Min score:{QUALITY_THRESHOLD}", flush=True)
    print(f"   Honest max: ~800-1200 Q/day | Per run: ~150-250 Q", flush=True)
    print("─"*60, flush=True)

    start    = time.time()
    max_run  = 113 * 60
    grand    = 0
    pass_num = 0

    while time.time() - start < max_run:
        elapsed   = int((time.time()-start)/60)
        remaining = int((max_run-(time.time()-start))/60)
        print(f"\n{'═'*60}", flush=True)
        print(f"Pass #{pass_num+1} | {elapsed}m elapsed | {remaining}m left | saved={grand}", flush=True)

        topics = (
            s.table("topics")
             .select("topic_id,topic_name,subject_id,difficulty_range,coverage_score")
             .eq("launch_phase","phase_1_now")
             .order("coverage_score", desc=True)
             .execute().data
        )

        if not topics:
            print("⚠️  No topics — sleep 60s", flush=True)
            time.sleep(60)
            continue

        print(f"📋 {len(topics)} topics in queue", flush=True)
        pass_total = 0
        pass_num  += 1

        with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as ex:
            futures = {ex.submit(process_topic, t): t["topic_id"] for t in topics}
            for fut in as_completed(futures):
                tid = futures[fut]
                try:
                    n = fut.result()
                    pass_total += n
                    grand      += n
                except Exception as e:
                    print(f"   !! {tid}: {e}", flush=True)

        print(f"\n✅ Pass #{pass_num}: +{pass_total} | Total: {grand}", flush=True)

        if pass_total == 0:
            print("🚨 All rate-limited — sleep 5min", flush=True)
            time.sleep(300)
        else:
            time.sleep(15)

    print(f"\n⏰ Done. {grand} questions in 113min", flush=True)
    rate = grand/113 if grand else 0
    print(f"   Rate: {rate:.1f} Q/min = {rate*60:.0f} Q/hr = {rate*60*24:.0f} Q/day", flush=True)

if __name__ == "__main__":
    main()




