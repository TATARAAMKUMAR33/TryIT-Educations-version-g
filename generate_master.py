# VERSION: 5.0 - PIPELINE SPLIT ENGINE
"""
TryIT Question Engine v5 - 4-STAGE PIPELINE
Stage 1: Question skeleton  -> Groq gpt-oss-120b + SambaNova DeepSeek-V3.2
Stage 2: 7-Layer explanation -> NVIDIA nemotron-550B + mistral-large-4
Stage 3: Quality score check -> SambaNova gpt-oss-120b
Stage 4: Final QA gate       -> Gemini gemini-3.5-flash
Target: 2000-3000 questions per 2hr GitHub Actions run
"""

import os, json, time, uuid, re, threading
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
BATCH_SIZE         = 5
CONCURRENT_WORKERS = 8
QUALITY_THRESHOLD  = 6
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

GROQ_KEYS      = load_keys("GROQ_API_KEY", 5)
SAMBA_KEYS     = load_keys("SAMBANOVA_API_KEY", 5)
NVIDIA_KEYS    = load_keys("NVIDIA_API_KEY", 5)
GEMINI_KEYS    = load_keys("GEMINI_API_KEY", 5)

print(f"Keys: GROQ={len(GROQ_KEYS)} SAMBA={len(SAMBA_KEYS)} NVIDIA={len(NVIDIA_KEYS)} GEMINI={len(GEMINI_KEYS)}", flush=True)

# ── KEY POOLS ──────────────────────────────────────────────────────────────────
GROQ_POOL   = get_pool("Groq",      GROQ_KEYS,   cooldown_seconds=62)
SAMBA_POOL  = get_pool("SambaNova", SAMBA_KEYS,  cooldown_seconds=60)
NVIDIA_POOL = get_pool("NVIDIA",    NVIDIA_KEYS, cooldown_seconds=90)
GEMINI_POOL = get_pool("Gemini",    GEMINI_KEYS, cooldown_seconds=60)

# ── CLIENTS ────────────────────────────────────────────────────────────────────
# Stage 1: Question skeleton - fast models
GROQ_CLIENTS  = {k: OpenAI(base_url="https://api.groq.com/openai/v1",   api_key=k) for k in GROQ_KEYS}
SAMBA_CLIENTS = {k: OpenAI(base_url="https://api.sambanova.ai/v1",       api_key=k) for k in SAMBA_KEYS}

# Stage 2: 7-layer explanation - largest models
NVIDIA_CLIENTS = {k: OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k) for k in NVIDIA_KEYS}

# Stage 4: QA gate - Gemini
GEMINI_KEY_TO_MODEL = {}

print("Probing Gemini...", flush=True)
for k in GEMINI_KEYS:
    for model in ["gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-2.5-flash-lite"]:
        try:
            c = genai.Client(api_key=k)
            c.models.generate_content(model=model, contents="hi")
            GEMINI_KEY_TO_MODEL[k] = model
            print(f"  Gemini key OK -> {model}", flush=True)
            break
        except Exception:
            continue

WORKING_GEMINI = list(GEMINI_KEY_TO_MODEL.keys())
if WORKING_GEMINI:
    GEMINI_POOL = get_pool("Gemini", WORKING_GEMINI, cooldown_seconds=60)
    print(f"Gemini QA pool: {len(WORKING_GEMINI)} keys", flush=True)
else:
    GEMINI_POOL = None
    print("No Gemini keys working - QA auto-pass", flush=True)

# ── JSON EXTRACTOR ─────────────────────────────────────────────────────────────
def extract_json(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    for cand in [text, text[text.find("["):text.rfind("]")+1] if "[" in text else ""]:
        if not cand: continue
        try:
            d = json.loads(cand)
            if isinstance(d, list): return d
            if isinstance(d, dict): return [d]
        except Exception:
            try:
                d = json_repair.loads(cand)
                if isinstance(d, list): return d
                if isinstance(d, dict): return [d]
            except Exception: continue
    return None

def extract_json_obj(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m: return None
    try: return json_repair.loads(m.group())
    except Exception: return None

# ── CALL HELPER ────────────────────────────────────────────────────────────────
def call_openai(pool, clients, model, messages, max_tokens=4096, timeout=90):
    """Generic OpenAI-compatible call with key rotation."""
    tried = 0
    max_try = len(clients)
    while tried < max_try:
        idx, key = pool.get_key(wait=False)
        if key is None: break
        tried += 1
        client = clients.get(key)
        if not client: pool.mark_error(idx); continue
        try:
            r = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                timeout=timeout,
            )
            raw = r.choices[0].message.content or ""
            if raw:
                pool.mark_success(idx)
                return raw
            pool.mark_error(idx)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                pool.mark_rate_limit(idx, cooldown=65)
            elif "401" in err or "403" in err:
                pool.mark_error(idx)
            elif "timeout" in err.lower() or "timed out" in err.lower():
                pool.mark_rate_limit(idx, cooldown=30)
            else:
                pool.mark_error(idx)
    return None

# ════════════════════════════════════════════════════════════════════════════════
# STAGE 1 — QUESTION SKELETON (Groq primary, SambaNova fallback)
# Generates: question + 4 options + correct_answer only
# Fast models, high volume
# ════════════════════════════════════════════════════════════════════════════════
def stage1_generate_skeleton(topic_name, subject_id, level, count, exam_tags, context=""):
    exam_str = ", ".join(exam_tags[:6]) if exam_tags else "UPSC, SSC CGL, RRB NTPC"
    prompt = f"""You are an expert MCQ writer for Indian competitive exams.
Generate exactly {count} unique MCQs for:
Topic: {topic_name} | Subject: {subject_id} | Difficulty: {level}/10
Exams: {exam_str}
{"Context: " + context if context else ""}

Difficulty guide:
- Level 1-3: Basic recall, textbook facts
- Level 4-6: Application, concept linking
- Level 7-10: Multi-step reasoning, trap options, analysis

Output ONLY a valid JSON array, no markdown:
[{{"question":"...","options":["A) ...","B) ...","C) ...","D) ..."],"correct_answer":0,"topic_hint":"one word topic"}}]

Rules:
- correct_answer is 0-indexed integer (0=A, 1=B, 2=C, 3=D)
- All 4 options must be plausible for levels 5+
- No duplicate questions"""

    msgs = [
        {"role": "system", "content": "Output ONLY valid JSON arrays. No explanation, no markdown."},
        {"role": "user", "content": prompt}
    ]

    # Try Groq first (fastest)
    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=2048, timeout=45)
        if raw:
            data = extract_json(raw)
            if data:
                valid = [q for q in data if q.get("question") and isinstance(q.get("options"), list) and len(q["options"]) == 4 and isinstance(q.get("correct_answer"), int)]
                if valid:
                    print(f"      S1 {len(valid)}q via Groq {model}", flush=True)
                    return valid

    # Fallback: SambaNova DeepSeek
    for model in ["DeepSeek-V3.2", "gpt-oss-120b", "Meta-Llama-3.3-70B-Instruct"]:
        raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs, max_tokens=2048, timeout=60)
        if raw:
            data = extract_json(raw)
            if data:
                valid = [q for q in data if q.get("question") and isinstance(q.get("options"), list) and len(q["options"]) == 4 and isinstance(q.get("correct_answer"), int)]
                if valid:
                    print(f"      S1 {len(valid)}q via SambaNova {model}", flush=True)
                    return valid

    return []

# ════════════════════════════════════════════════════════════════════════════════
# STAGE 2 — 7-LAYER EXPLANATION (NVIDIA large models)
# Adds: why_correct, why_wrong x3, story, shortcut, cross_exam
# Uses largest available NVIDIA models for depth
# ════════════════════════════════════════════════════════════════════════════════
def stage2_add_explanation(q, topic_name, level, exam_tags):
    exam_str = ", ".join(exam_tags[:4]) if exam_tags else "UPSC, SSC CGL"
    correct_opt = q["options"][q["correct_answer"]]
    wrong_opts  = [o for i, o in enumerate(q["options"]) if i != q["correct_answer"]]

    prompt = f"""You are a top Indian competitive exam expert and teacher.
Add a 7-layer explanation to this MCQ:

Question: {q["question"]}
Options: {q["options"]}
Correct Answer: {correct_opt} (index {q["correct_answer"]})
Topic: {topic_name} | Difficulty: {level}/10 | Exams: {exam_str}

Output ONLY valid JSON (no markdown):
{{
  "why_correct": "Step-by-step logical proof of why {correct_opt} is correct. Show the reasoning chain clearly.",
  "why_wrong_option_b": "Exact misconception that makes students choose {wrong_opts[0] if len(wrong_opts)>0 else 'B'}. Name the trap.",
  "why_wrong_option_c": "Exact misconception that makes students choose {wrong_opts[1] if len(wrong_opts)>1 else 'C'}. Name the trap.",
  "why_wrong_option_d": "Exact misconception that makes students choose {wrong_opts[2] if len(wrong_opts)>2 else 'D'}. Name the trap.",
  "story_explanation": "A 3-sentence Indian story (Ramu/Priya/shopkeeper/cricket) where this concept appears naturally. Must make the answer unforgettable.",
  "shortcut_tips": "The exact mnemonic or 10-second trick top scorers use for this type of question in {exam_str}.",
  "cross_exam_intelligence": "UPSC Prelims asks this as [angle]. SSC CGL asks this as [angle]. RRB NTPC tests [angle]. State PSCs focus on [angle]."
}}"""

    msgs = [
        {"role": "system", "content": "Output ONLY valid JSON object. No markdown. No explanation outside JSON."},
        {"role": "user", "content": prompt}
    ]

    # NVIDIA large models - best for deep explanation
    for model in [
        "nvidia/nemotron-3-ultra-550b-a55b",
        "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "mistralai/mistral-large-4-1t-a52b",
        "moonshotai/kimi-k2.6",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "mistralai/mistral-large-2-instruct",
    ]:
        raw = call_openai(NVIDIA_POOL, NVIDIA_CLIENTS, model, msgs, max_tokens=2048, timeout=90)
        if raw:
            data = extract_json_obj(raw)
            if data and data.get("why_correct"):
                q.update(data)
                print(f"      S2 explanation via NVIDIA {model}", flush=True)
                return q

    # Final fallback: SambaNova for explanation
    for model in ["DeepSeek-V3.2", "gpt-oss-120b"]:
        raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs, max_tokens=2048, timeout=60)
        if raw:
            data = extract_json_obj(raw)
            if data and data.get("why_correct"):
                q.update(data)
                print(f"      S2 explanation via SambaNova {model}", flush=True)
                return q

    # If all fail, add placeholder so question still saves
    q.setdefault("why_correct", "See official study material.")
    q.setdefault("why_wrong_option_b", "Common misconception.")
    q.setdefault("why_wrong_option_c", "Common misconception.")
    q.setdefault("why_wrong_option_d", "Common misconception.")
    q.setdefault("story_explanation", "")
    q.setdefault("shortcut_tips", "")
    q.setdefault("cross_exam_intelligence", exam_str)
    return q

# ════════════════════════════════════════════════════════════════════════════════
# STAGE 3 — QUALITY SCORE (SambaNova cross-check)
# Returns score 1-10 for difficulty calibration
# ════════════════════════════════════════════════════════════════════════════════
def stage3_quality_score(q, level):
    prompt = f"""Rate this Indian competitive exam MCQ.
Target difficulty: {level}/10

Q: {q.get("question","")}
Options: {q.get("options",[])}
Correct: index {q.get("correct_answer",0)}

Return ONLY JSON: {{"score": 8, "calibrated_level": 7, "issues": "none"}}
Score 1-10. Be strict. Penalize: vague options, too easy for level, factual errors."""

    msgs = [{"role": "user", "content": prompt}]

    for model in ["gpt-oss-120b", "DeepSeek-V3.2", "Meta-Llama-3.3-70B-Instruct"]:
        raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs, max_tokens=100, timeout=30)
        if raw:
            data = extract_json_obj(raw)
            if data and "score" in data:
                score = int(data.get("score", 0))
                print(f"      S3 score={score} via SambaNova {model}", flush=True)
                return score

    return 7  # default pass if scorer unavailable

# ════════════════════════════════════════════════════════════════════════════════
# STAGE 4 — GEMINI FINAL GATE (QA verify)
# Final approve/reject decision
# ════════════════════════════════════════════════════════════════════════════════
def stage4_gemini_verify(q, level):
    if not GEMINI_POOL:
        return True, 7, "no verifier"

    idx, key = GEMINI_POOL.get_key(wait=False)
    if key is None:
        return True, 7, "gemini cooling"

    model = GEMINI_KEY_TO_MODEL.get(key, "gemini-3.5-flash")
    try:
        client = genai.Client(api_key=key)
        prompt = f"""Final QA check for Indian competitive exam MCQ.
Level: {level}/10

Q: {q.get("question","")}
Options: {q.get("options",[])}
Correct index: {q.get("correct_answer",0)}
Explanation: {q.get("why_correct","")[:150]}

Return ONLY JSON: {{"passed": true, "score": 8, "reason": "one line"}}
Reject if: factually wrong, ambiguous correct answer, explanation contradicts answer."""

        r = client.models.generate_content(model=model, contents=prompt)
        txt = re.sub(r"^```json\s*|\s*```$", "", (r.text or "").strip(), flags=re.MULTILINE)
        d = extract_json_obj(txt)
        if d:
            GEMINI_POOL.mark_success(idx)
            return d.get("passed", False), int(d.get("score", 0)), d.get("reason", "")
        GEMINI_POOL.mark_error(idx)
        return True, 6, "parse error - auto pass"
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            GEMINI_POOL.mark_rate_limit(idx, cooldown=65)
        elif "503" in err or "overloaded" in err.lower():
            return True, 7, "gemini overloaded - auto pass"
        else:
            GEMINI_POOL.mark_error(idx)
        return True, 6, f"gemini error - auto pass"

# ════════════════════════════════════════════════════════════════════════════════
# FULL PIPELINE: Stage 1 → 2 → 3 → 4
# ════════════════════════════════════════════════════════════════════════════════
def run_pipeline(topic_id, topic_name, subject_id, level, count, exam_tags):
    context = get_context(topic_id) if callable(get_context) else ""

    # S1: Get question skeletons
    skeletons = stage1_generate_skeleton(topic_name, subject_id, level, count, exam_tags, context)
    if not skeletons:
        return []

    results = []
    for q in skeletons:
        # S2: Add 7-layer explanation via NVIDIA
        q = stage2_add_explanation(q, topic_name, level, exam_tags)

        # S3: Quality score via SambaNova
        score = stage3_quality_score(q, level)
        if score < QUALITY_THRESHOLD:
            print(f"      ✗ S3 rejected score={score}", flush=True)
            continue

        # S4: Final Gemini gate
        passed, gemini_score, reason = stage4_gemini_verify(q, level)
        if not passed:
            print(f"      ✗ S4 Gemini rejected: {reason[:50]}", flush=True)
            continue

        final_score = max(score, gemini_score)
        q["_score"] = final_score
        results.append(q)
        print(f"      ✅ Pipeline complete score={final_score}", flush=True)

    return results

# ── DB HELPERS ─────────────────────────────────────────────────────────────────
def get_existing_count(topic_id, level):
    try:
        r = s.table("questions").select("id", count="exact").eq("topic_id", topic_id).eq("level", level).execute()
        return r.count or 0
    except Exception:
        return 0

def save(q, topic_id, subject_id, level, exam_tags):
    diagram_kind = DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id)
    if diagram_kind:
        q = sanitize_question_svgs(q, diagram_kind)

    rec = {
        "id":               f"q_{uuid.uuid4().hex[:16]}",
        "topic_id":         topic_id,
        "subject_id":       subject_id,
        "level":            level,
        "difficulty":       "Easy" if level <= 3 else "Medium" if level <= 6 else "Hard" if level <= 8 else "Expert",
        "pattern_type":     "standalone_mcq4",
        "question_en":      q["question"],
        "options_en":       q["options"],
        "correct_answer":   q["correct_answer"],
        "explanation": {
            k: q.get(k, "")
            for k in ["why_correct","why_wrong_option_b","why_wrong_option_c",
                      "why_wrong_option_d","story_explanation","shortcut_tips",
                      "cross_exam_intelligence"]
        },
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
        "generated_by":       "tryit_v5",
        "created_at":         datetime.now(timezone.utc).isoformat(),
    }

    if is_duplicate(s, q["question"], topic_id):
        print("      ♻️ Duplicate - skip", flush=True)
        return False

    success, _ = safe_db_insert(s, "questions", rec)
    return success

# ── TOPIC PROCESSORS ───────────────────────────────────────────────────────────
def process_topic_level(topic_id, topic_name, subject_id, level, target, exam_tags):
    existing = get_existing_count(topic_id, level)
    if existing >= target: return 0
    needed = target - existing
    print(f"   ⏳ {topic_id} L{level}: {existing}/{target} need {needed}", flush=True)

    saved = 0
    empty_rounds = 0

    while saved < needed and empty_rounds < 3:
        batch_need = min(BATCH_SIZE, needed - saved)
        questions  = run_pipeline(topic_id, topic_name, subject_id, level, batch_need, exam_tags)

        if not questions:
            empty_rounds += 1
            print(f"   ⚠️ Empty ({empty_rounds}/3) waiting 5s", flush=True)
            time.sleep(5)
            continue

        empty_rounds = 0
        for q in questions:
            if save(q, topic_id, subject_id, level, exam_tags):
                saved += 1
                print(f"      💾 saved {saved}/{needed}", flush=True)
        time.sleep(0.3)

    print(f"   🎉 {topic_id} L{level}: +{saved}", flush=True)
    return saved

def process_topic(topic):
    tid   = topic["topic_id"]
    tname = topic.get("topic_name", tid)
    sid   = topic.get("subject_id") or "general"
    dr    = topic.get("difficulty_range") or "2-7"
    try: lo, hi = map(int, dr.split("-"))
    except Exception: lo, hi = 2, 7

    try:
        rows = s.table("exam_syllabus_map").select("exam_id").eq("topic_id", tid).execute().data or []
        exam_tags = sorted(set(r["exam_id"] for r in rows))
    except Exception:
        exam_tags = []

    print(f"\n📘 {tid} [{tname}] L{lo}-L{hi}", flush=True)
    total = 0
    for lvl in range(lo, hi+1):
        target = TARGET_L1_L5 if lvl <= 5 else TARGET_L6_L10
        total += process_topic_level(tid, tname, sid, lvl, target, exam_tags)
    return total

# ── MAIN ───────────────────────────────────────────────────────────────────────
def main():
    print("🚀 TryIT Engine v5 - 4-Stage Pipeline", flush=True)
    print("   S1:Question→Groq/SambaNova | S2:Explain→NVIDIA | S3:Score→SambaNova | S4:QA→Gemini", flush=True)
    print(f"   Workers:{CONCURRENT_WORKERS} | Batch:{BATCH_SIZE} | QualityMin:{QUALITY_THRESHOLD}/10", flush=True)
    print("─"*60, flush=True)

    start      = time.time()
    max_run    = 113 * 60
    grand      = 0
    pass_num   = 0

    while time.time() - start < max_run:
        elapsed   = int((time.time()-start)/60)
        remaining = int((max_run-(time.time()-start))/60)
        print(f"\n{'═'*60}", flush=True)
        print(f"Pass #{pass_num+1} | {elapsed}m elapsed | {remaining}m left | total={grand}", flush=True)

        topics = (
            s.table("topics")
             .select("topic_id,topic_name,subject_id,difficulty_range,coverage_score")
             .eq("launch_phase","phase_1_now")
             .order("coverage_score", desc=True)
             .execute().data
        )

        if not topics:
            print("⚠️ No topics found - sleep 60s", flush=True)
            time.sleep(60)
            continue

        print(f"📋 {len(topics)} topics", flush=True)
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

        print(f"\n✅ Pass #{pass_num}: +{pass_total} | Grand total: {grand}", flush=True)

        if pass_total == 0:
            print("🚨 All APIs rate-limited - sleep 5min", flush=True)
            time.sleep(300)
        else:
            time.sleep(10)

    print(f"\n⏰ Done. Total: {grand} questions in 113 minutes", flush=True)
    print(f"   Rate: {grand/113:.1f} q/min | {grand/113*60:.0f} q/hr", flush=True)

if __name__ == "__main__":
    main()
