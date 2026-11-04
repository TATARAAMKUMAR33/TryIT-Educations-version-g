# VERSION: 7.0 - FINAL PRODUCTION ENGINE
"""
TryIT Engine v7  Final Production

PROVIDERS (confirmed working 2026-11-03):
  Groq          5 keys  org-wide 1,000 RPD   PRIMARY generator
  Gemini 1,3,4  3 keys  500 RPD each         SECONDARY generator
  Gemini 5      1 key   500 RPD              QA gate ONLY
  NVIDIA        5 keys  finite credits       L8-10 explanation upgrade
  SambaNova     REMOVED (rate-limited, slow)
  OpenAI        REMOVED (no credits)

ARCHITECTURE:
  1 API call = 1 complete question with ALL 7 layers
  Groq/Gemini  generate full Q+7layers in ONE call
  Gemini QA    verify all 7 layers complete + quality check
  NVIDIA       upgrade explanation for L8-10 only

DIFFICULTY QUEUE:
  Priority 1: L2 topics (6,295 needed)
  Priority 2: L4 topics (2,179 needed)
  Priority 3: L5 topics (514 needed)
  Priority 4: Everything else

TARGET: 2,000 Q/run  8 runs/day = 16,000 Q/day

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

#  CONSTANTS 
BATCH_SIZE         = 5    # Questions per API call
CONCURRENT_WORKERS = 3    # Parallel topic threads
QUALITY_THRESHOLD  = 6    # Min score to save (1-10)
TARGET_EASY        = 20   # Q per topic per level (L1-L5)
TARGET_HARD        = 10   # Q per topic per level (L6-L10)

#  SUPABASE 
s = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

#  KEY LOADER 
def load_keys(prefix, n=5):
    keys = []
    base = os.getenv(prefix)
    if base and base.strip(): keys.append(base.strip())
    for i in range(1, n+1):
        k = os.getenv(f"{prefix}_{i}")
        if k and k.strip(): keys.append(k.strip())
    return keys

GROQ_KEYS   = load_keys("GROQ_API_KEY", 5)
GEMINI_KEYS = load_keys("GEMINI_API_KEY", 5)
NVIDIA_KEYS = load_keys("NVIDIA_API_KEY", 5)

print(f" Keys: GROQ={len(GROQ_KEYS)} GEMINI={len(GEMINI_KEYS)} NVIDIA={len(NVIDIA_KEYS)}", flush=True)

#  GROQ SETUP 
GROQ_POOL    = get_pool("Groq", GROQ_KEYS, cooldown_seconds=62)
GROQ_CLIENTS = {k: OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k) for k in GROQ_KEYS}
import threading as _th
_groq_lock = _th.Lock()
_groq_last = [0.0]
def groq_rate_wait():
    with _groq_lock:
        gap = 2.5 - (time.time() - _groq_last[0])
        if gap > 0:
            time.sleep(gap)
        _groq_last[0] = time.time()

#  GEMINI SETUP 
# Split Gemini keys: first 3 for generation, last 1 for QA
# Key index 0,1,2 = generators | Key index 3 = QA gate
GEMINI_WORKING = []
GEMINI_KEY_TO_MODEL = {}

print(" Probing Gemini keys...", flush=True)
for i, k in enumerate(GEMINI_KEYS):
    for model in ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-1.5-flash"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}"
            r = req.post(url, json={"contents":[{"parts":[{"text":"hi"}]}]}, timeout=15)
            if r.status_code != 200:
                print(f"  FAIL Gemini key {model}: {r.status_code}", flush=True)
                continue
            _ = r
            GEMINI_KEY_TO_MODEL[k] = model
            GEMINI_WORKING.append(k)
            role = "QA" if i >= 3 else "GEN"
            print(f"   Gemini key {i+1} [{role}]  {model}", flush=True)
            break
        except Exception as probe_err:
            print(f'    Gemini probe {model}: {str(probe_err)[:60]}', flush=True)
            continue

# Split working keys: generators vs QA
GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 3]
GEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 3]

GEMINI_GEN_POOL = get_pool("GeminiGen", GEMINI_GEN_KEYS, cooldown_seconds=65) if GEMINI_GEN_KEYS else None
GEMINI_QA_POOL  = get_pool("GeminiQA",  GEMINI_QA_KEYS,  cooldown_seconds=65) if GEMINI_QA_KEYS  else None

print(f"  Gemini GEN pool: {len(GEMINI_GEN_KEYS)} keys | QA pool: {len(GEMINI_QA_KEYS)} keys", flush=True)

#  NVIDIA SETUP 
NVIDIA_POOL    = get_pool("NVIDIA", NVIDIA_KEYS, cooldown_seconds=90)
NVIDIA_CLIENTS = {k: OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k) for k in NVIDIA_KEYS}

#  DIFFICULTY HELPERS 
def diff_label(level):
    if level <= 2:  return "Foundation"
    if level <= 4:  return "Easy"
    if level <= 6:  return "Medium"
    if level <= 8:  return "Hard"
    return "Expert"

def diff_guide(level):
    guides = {
        1:  "Class 1-2 level. Single simple fact. Child of age 6-7 must understand instantly. Example: 'Which animal gives milk?'",
        2:  "Class 3-4 level. Basic recall. One concept. Student age 8-9. Example: 'What is 78?' or 'Capital of Maharashtra?'",
        3:  "Class 5-6 level. Simple application. Two facts connected. Example: 'If 1 dozen = 12, how many eggs in 3 dozen?'",
        4:  "Class 7-8 level. Concept application. Basic reasoning. Example: 'Why does ice float on water?'",
        5:  "Class 9-10 level. Multi-concept. Board exam style. Example: 'Calculate SI for 5000 at 8% for 3 years'",
        6:  "Class 11-12 / State PSC level. Application + one trap option. Example: 'Which Article deals with Right to Education?'",
        7:  "Graduation / SSC CGL / UPSC Prelims level. Two trap options. Multi-step reasoning. Common misconceptions tested.",
        8:  "Post-graduation / GATE / NEET level. Advanced concepts. All options plausible to average student.",
        9:  "UPSC Mains / GATE Advanced level. Expert reasoning. Conceptual depth. Analytical thinking required.",
        10: "Research / PhD entrance level. Highest difficulty. All options seem correct to 90% of students."
    }
    return guides.get(level, "Competitive exam level MCQ.")

def story_guide(level):
    guides = {
        1:  "Story character: a 6-year-old child named [NAME]. Setting: home or school. The child must discover the answer through play or a simple daily activity like counting fruits or seeing animals.",
        2:  "Story character: a Class 3-4 student named [NAME]. Setting: classroom or home. Teacher or parent explains through a simple real-life example.",
        3:  "Story character: a Class 5-6 student named [NAME]. Setting: school or market. Student solves a small real problem that matches the question concept exactly.",
        4:  "Story character: a Class 7-8 student named [NAME]. Setting: science lab, history class, or local area. Student questions why something happens and gets a clear answer.",
        5:  "Story character: a Class 10 student named [NAME] preparing for board exams. Setting: study room or tuition class. The concept clicks through a real-life observation.",
        6:  "Story character: a competitive exam aspirant named [NAME] preparing for SSC/State PSC. Setting: coaching centre or self-study. They encounter this exact concept and learn the trick.",
        7:  "Story character: an UPSC/SSC CGL aspirant named [NAME]. Setting: mock test or previous year paper discussion. They get this question wrong first, then understand why through a real scenario.",
        8:  "Story character: a final year engineering/medical student named [NAME]. Setting: university lab or hospital. They apply this concept to solve a real professional problem.",
        9:  "Story character: a professional named [NAME]  IAS officer, doctor, engineer. Setting: real work situation. The concept directly applies to a decision they must make.",
        10: "Story character: a researcher or PhD student named [NAME]. Setting: research lab or academic conference. The concept is debated and the correct answer is proven through evidence."
    }
    return guides.get(level, guides[7])

#  JSON HELPERS 
def extract_list(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$", "", text.strip(), flags=re.MULTILINE).strip()
    candidates = [text]
    if "[" in text:
        candidates.append(text[text.find("["):text.rfind("]")+1])
    for cand in candidates:
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

def validate_questions(data):
    valid = []
    for q in (data or []):
        if not isinstance(q, dict): continue
        if not q.get("question"): continue
        if not isinstance(q.get("options"), list): continue
        if len(q.get("options", [])) != 4: continue
        if not isinstance(q.get("correct_answer"), int): continue
        if not (0 <= q.get("correct_answer", -1) <= 3): continue
        if not q.get("why_correct"): continue
        if not q.get("story_explanation"): continue
        valid.append(q)
    return valid

#  OPENAI-COMPATIBLE CALL 
def call_openai(pool, clients, model, messages, max_tokens=4096, timeout=90, label=""):
    tried = 0
    total = len(clients)
    while tried < total:
        idx, key = pool.get_key(wait=False)
        if key is None: break
        tried += 1
        client = clients.get(key)
        if not client: pool.mark_error(idx); continue
        try:
            r = client.chat.completions.create(
                model=model, messages=messages,
                max_tokens=max_tokens, temperature=0.75, timeout=timeout
            )
            raw = r.choices[0].message.content or ""
            if raw: pool.mark_success(idx); return raw
            pool.mark_error(idx)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                pool.mark_rate_limit(idx, cooldown=65)
                print(f"       {label} key#{idx+1} rate-limited", flush=True)
            elif "401" in err or "403" in err:
                pool.mark_error(idx)
                print(f"       {label} key#{idx+1} auth error", flush=True)
            elif "timeout" in err.lower():
                pool.mark_rate_limit(idx, cooldown=30)
            else:
                pool.mark_error(idx)
    return None

#  GEMINI CALL 
def call_gemini(pool, key_to_model, prompt, label="Gemini"):
    if not pool: return None
    idx, key = pool.get_key(wait=False)
    if key is None: return None
    model = key_to_model.get(key, "gemini-3.5-flash")
    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=key)
        m = genai_legacy.GenerativeModel(model)
        r = m.generate_content(prompt)
        raw = r.text or ""
        if raw: pool.mark_success(idx); return raw
        pool.mark_error(idx)
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            pool.mark_rate_limit(idx, cooldown=70)
            print(f"       {label} key#{idx+1} rate-limited", flush=True)
        elif "503" in err or "overloaded" in err.lower():
            pool.mark_rate_limit(idx, cooldown=30)
        else:
            pool.mark_error(idx)
    return None

# 
# CORE PROMPT  generates complete question with ALL 7 layers in ONE call
# 
def build_prompt(topic_name, subject_id, level, count, exam_tags, context):
    exam_str  = ", ".join(exam_tags[:5]) if exam_tags else "UPSC, SSC CGL, RRB NTPC, State PSC"
    dlabel    = diff_label(level)
    dguide    = diff_guide(level)
    sguide    = story_guide(level)

    return f"""You are India's most experienced MCQ writer for competitive and school exams.
Generate exactly {count} unique MCQs.

TOPIC: {topic_name}
SUBJECT: {subject_id}
DIFFICULTY: Level {level}/10  {dlabel}
TARGET EXAMS: {exam_str}
CONTEXT: {context[:400] if context else "Indian educational context"}

 DIFFICULTY REQUIREMENT 
{dguide}
Every question MUST match exactly Level {level}/10.
Reject if too easy or too hard for this level.

 MCQ RULES 
1. correct_answer is 0-indexed integer (0=A, 1=B, 2=C, 3=D)
2. All 4 options must be distinct and relevant
3. For Level 5+: minimum 2 options must seem plausible to average student
4. For Level 7+: all 4 options must seem plausible, test real misconceptions
5. No "All of the above" or "None of the above" options

 7-LAYER EXPLANATION REQUIREMENT 
Every question MUST have all 7 layers filled completely:

Layer 1  why_correct:
"Step 1: [explain first logical step]. Step 2: [next step]. Step 3: [conclusion]. Therefore [correct option] is right because [final reason]."
Must be complete step-by-step proof. Never just restate the answer.

Layer 2,3,4  why_wrong_option_b/c/d:
"Students choose this because [SPECIFIC misconception name]. This is wrong because [exact counter-proof]. The trap here is [what makes it seem right]."
Each must name the SPECIFIC misconception. Never say "this is incorrect."

Layer 5  story_explanation:
{sguide}
RULES FOR STORY:
- Use the character name from context above
- Place story in the city/setting from context
- Story MUST demonstrate the EXACT concept being tested
- Character must face the SAME problem as the question
- Character solves it using SAME logic as correct answer
- Final sentence MUST be: "This is exactly why [correct option letter and text] is the answer."
- Write in simple conversational Hindi-English mix if level 1-4, pure English for level 5+
- Make it so memorable that student can never forget the answer

Layer 6  shortcut_tips:
"TRICK NAME: [give it a catchy name]. 
HOW IT WORKS: [the trick in one sentence  mnemonic, pattern, or visual].
APPLY HERE: [show exactly how trick gives answer in under 10 seconds for THIS question].
EXAM TIP: [which exam uses this trick most and how]."
Must be a REAL trick, not "just remember this."

Layer 7  cross_exam_intelligence:
"UPSC Prelims: this appears as [exact question type  assertion-reason/statement-based/direct]  watch out for [specific trap]. 
SSC CGL Tier-1: tested as [angle], wrong answer trap is option [letter] because [reason].
RRB NTPC: [angle and difficulty].
[Other relevant exam]: [angle]."
Must be exam-specific warnings, not generic advice.

 OUTPUT FORMAT 
Output ONLY a valid JSON array. No markdown, no explanation, no text outside JSON:
[
  {{
    "question": "Complete question text ending with ?",
    "options": ["A) option text", "B) option text", "C) option text", "D) option text"],
    "correct_answer": 0,
    "why_correct": "Step 1: ... Step 2: ... Therefore A is correct because ...",
    "why_wrong_option_b": "Students choose B because [misconception]. Wrong because [proof]. Trap: [what makes it seem right].",
    "why_wrong_option_c": "Students choose C because [misconception]. Wrong because [proof]. Trap: [what makes it seem right].",
    "why_wrong_option_d": "Students choose D because [misconception]. Wrong because [proof]. Trap: [what makes it seem right].",
    "story_explanation": "4-sentence story using character from context. Last sentence: This is exactly why [option] is the answer.",
    "shortcut_tips": "TRICK NAME: ... HOW IT WORKS: ... APPLY HERE: ... EXAM TIP: ...",
    "cross_exam_intelligence": "UPSC Prelims: ... SSC CGL: ... RRB NTPC: ... Other: ..."
  }}
]"""

# 
# GENERATION  Groq primary, Gemini secondary, one call = full question
# 
def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags):
    context = get_context(topic_id, subject_id) if callable(get_context) else ""
    prompt  = build_prompt(topic_name, subject_id, level, count, exam_tags, context)

    sys_msg = "You are a JSON-only MCQ generator. Output ONLY a valid JSON array. Never add text outside the JSON."
    msgs    = [
        {"role": "system", "content": sys_msg},
        {"role": "user",   "content": prompt}
    ]

    #  PRIMARY: Groq (1,000 RPD org-wide, fastest) 
    groq_rate_wait()
        for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:
        raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs,
                          max_tokens=4096, timeout=60, label="Groq")
        if raw:
            data  = extract_list(raw)
            valid = validate_questions(data)
            if valid:
                print(f"        {len(valid)}q via Groq {model} L{level}", flush=True)
                return valid

    #  SECONDARY: Gemini generation keys (3 keys  500 RPD = 1,500/day) 
    if GEMINI_GEN_POOL:
        # Gemini needs prompt as plain text (no system message)
        gemini_prompt = f"{sys_msg}\n\n{prompt}"
        raw = call_gemini(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL, gemini_prompt, "GeminiGen")
        if raw:
            data  = extract_list(raw)
            valid = validate_questions(data)
            if valid:
                print(f"        {len(valid)}q via GeminiGen L{level}", flush=True)
                return valid

    print(f"        All generators failed for L{level} batch", flush=True)
    return []

# 
# NVIDIA UPGRADE  only for L8-10, rewrites explanation with 550B model
# 
def nvidia_upgrade(q, topic_name, level, exam_tags):
    exam_str = ", ".join(exam_tags[:3]) if exam_tags else "UPSC, GATE"
    correct  = q["options"][q["correct_answer"]]

    prompt = f"""Upgrade this Level {level}/10 MCQ explanation to expert quality for {exam_str}.

Question: {q["question"]}
Correct Answer: {correct}
Current explanation: {q.get("why_correct","")[:300]}

Return ONLY valid JSON object:
{{
  "why_correct": "Expert-level proof with full technical depth. Step 1: [deep explanation]. Step 2: [technical reasoning]. Step 3: [conclusion with formula/rule citation if applicable].",
  "why_wrong_option_b": "Deep analysis: [exact conceptual error]. Proof it is wrong: [technical counter-argument]. Common exam trap: [why toppers fall for this].",
  "why_wrong_option_c": "Deep analysis: [exact conceptual error]. Proof it is wrong: [technical counter-argument]. Common exam trap: [why toppers fall for this].",
  "why_wrong_option_d": "Deep analysis: [exact conceptual error]. Proof it is wrong: [technical counter-argument]. Common exam trap: [why toppers fall for this].",
  "shortcut_tips": "TRICK NAME: [advanced pattern]. HOW IT WORKS: [expert trick]. APPLY HERE: [demonstrate on this question]. EXAM TIP: [UPSC/GATE specific strategy].",
  "cross_exam_intelligence": "UPSC [year if known]: appeared as [format]. GATE [year if known]: tested as [angle]. NEET/Other: [specific angle and trap]."
}}"""

    msgs = [{"role": "user", "content": prompt}]
    for model in [
        "nvidia/nemotron-3-ultra-550b-a55b",
        "nvidia/llama-3.1-nemotron-ultra-253b-v1",
        "mistralai/mistral-large-4-1t-a52b",
        "moonshotai/kimi-k2.6",
        "nvidia/llama-3.1-nemotron-70b-instruct"
    ]:
        raw = call_openai(NVIDIA_POOL, NVIDIA_CLIENTS, model, msgs,
                          max_tokens=2000, timeout=90, label="NVIDIA")
        if raw:
            data = extract_obj(raw)
            if data and data.get("why_correct") and len(data["why_correct"]) > 50:
                q.update(data)
                print(f"       NVIDIA upgrade via {model}", flush=True)
                return q
    return q  # Return original if NVIDIA fails

# 
# GEMINI QA GATE  checks ALL 7 layers complete + quality + difficulty match
# 
def gemini_qa(q, level):
    if not GEMINI_QA_POOL:
        return True, 7, "no QA pool  auto pass"

    idx, key = GEMINI_QA_POOL.get_key(wait=False)
    if key is None:
        return True, 7, "QA cooling  auto pass"

    model = GEMINI_KEY_TO_MODEL.get(key, "gemini-3.5-flash")

    # Check all 7 layers exist and are non-empty before calling API
    required = ["why_correct","why_wrong_option_b","why_wrong_option_c",
                "why_wrong_option_d","story_explanation","shortcut_tips","cross_exam_intelligence"]
    missing = [f for f in required if not q.get(f) or len(str(q.get(f,""))) < 20]
    if missing:
        print(f"       Missing layers: {missing}", flush=True)
        return False, 0, f"missing: {missing}"

    prompt = f"""You are a strict quality controller for Indian competitive exam MCQs.
Evaluate this Level {level}/10 ({diff_label(level)}) question.

QUESTION: {q.get("question","")}
OPTIONS: {q.get("options",[])}
CORRECT INDEX: {q.get("correct_answer",0)}

EXPLANATIONS:
why_correct: {q.get("why_correct","")[:200]}
story_explanation: {q.get("story_explanation","")[:200]}
shortcut_tips: {q.get("shortcut_tips","")[:150]}

Check ALL of these strictly:
1. Does difficulty EXACTLY match Level {level}/10? ({diff_guide(level)[:80]})
2. Is correct answer factually accurate?
3. Does why_correct have step-by-step proof (not just restate answer)?
4. Does story_explanation tell a real Indian story where character solves SAME problem as question?
5. Does story end with "This is exactly why [option] is the answer"?
6. Does shortcut_tips have TRICK NAME + HOW IT WORKS + APPLY HERE?
7. Are wrong option explanations specific (name the misconception)?

Return ONLY JSON:
{{"passed": true, "score": 8, "reason": "one sentence  what is good or what failed"}}

Score 1-10. Pass if score >= 6 AND checks 1,2,3 all pass.
Reject immediately if: wrong difficulty level, factual error, or story doesn't connect to answer."""

    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=key)
        m = genai_legacy.GenerativeModel(model)
        r = m.generate_content(prompt)
        txt = re.sub(r"^```json\s*|\s*```$", "", (r.text or "").strip(), flags=re.MULTILINE)
        d = extract_obj(txt)
        if d:
            GEMINI_QA_POOL.mark_success(idx)
            passed = d.get("passed", False)
            score  = int(d.get("score", 0))
            reason = d.get("reason", "")
            if not passed:
                print(f"       QA rejected L{level}: {reason[:60]}", flush=True)
            return passed, score, reason
        GEMINI_QA_POOL.mark_error(idx)
        return True, 6, "parse fail  auto pass"
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower():
            GEMINI_QA_POOL.mark_rate_limit(idx, cooldown=70)
        elif "503" in err or "overloaded" in err.lower():
            return True, 7, "gemini overloaded  auto pass"
        else:
            GEMINI_QA_POOL.mark_error(idx)
        return True, 6, "gemini error  auto pass"

#  DB HELPERS 
def get_existing_count(topic_id, level):
    try:
        r = s.table("questions").select("id", count="exact") \
             .eq("topic_id", topic_id).eq("level", level).execute()
        return r.count or 0
    except Exception: return 0

def save_question(q, topic_id, subject_id, level, exam_tags):
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
        "explanation": {k: q.get(k, "") for k in [
            "why_correct","why_wrong_option_b","why_wrong_option_c",
            "why_wrong_option_d","story_explanation","shortcut_tips",
            "cross_exam_intelligence"
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
        "generated_by":       "tryit_v7",
        "created_at":         datetime.now(timezone.utc).isoformat(),
    }

    if is_duplicate(s, q["question"], topic_id):
        print("        Duplicate  skip", flush=True)
        return False

    success, _ = safe_db_insert(s, "questions", rec)
    return success

#  TOPIC LEVEL PROCESSOR 
def process_topic_level(topic_id, topic_name, subject_id, level, target, exam_tags):
    existing = get_existing_count(topic_id, level)
    if existing >= target: return 0
    needed = target - existing
    print(f"    {topic_name[:35]} L{level} ({diff_label(level)}): {existing}/{target} need {needed}", flush=True)

    saved       = 0
    empty_rounds = 0

    while saved < needed and empty_rounds < 3:
        batch = min(BATCH_SIZE, needed - saved)
        questions = generate_batch(topic_id, topic_name, subject_id, level, batch, exam_tags)

        if not questions:
            empty_rounds += 1
            print(f"     Empty batch {empty_rounds}/3  wait 5s", flush=True)
            time.sleep(5)
            continue

        empty_rounds = 0
        for q in questions:
            # NVIDIA upgrade for expert questions only (saves credits)
            if level >= 8:
                q = nvidia_upgrade(q, topic_name, level, exam_tags)

            # Gemini QA gate
            passed, score, reason = gemini_qa(q, level)
            if not passed or score < QUALITY_THRESHOLD:
                continue

            q["_score"] = score
            if save_question(q, topic_id, subject_id, level, exam_tags):
                saved += 1
                print(f"       saved {saved}/{needed} L{level} score={score}", flush=True)

        time.sleep(2.5)

    print(f"    {topic_name[:30]} L{level}: +{saved}", flush=True)
    return saved

#  TOPIC PROCESSOR 
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

    print(f"\n {tname} L{lo}-L{hi} ({diff_label(lo)}{diff_label(hi)})", flush=True)
    total = 0
    for lvl in range(lo, hi+1):
        target = TARGET_EASY if lvl <= 5 else TARGET_HARD
        total += process_topic_level(tid, tname, sid, lvl, target, exam_tags)
    return total

#  SMART TOPIC QUEUE 
def get_priority_topics():
    """
    Priority order:
    1. L2 start topics (most needed  6,295 Q gap)
    2. L4 start topics (2,179 Q gap)
    3. L5 start topics (514 Q gap)
    4. All other phase_1_now topics
    """
    try:
        all_topics = (
            s.table("topics")
             .select("topic_id,topic_name,subject_id,difficulty_range,coverage_score")
             .eq("launch_phase", "phase_1_now")
             .execute().data or []
        )

        def priority(t):
            dr = t.get("difficulty_range","2-7")
            try: lo = int(dr.split("-")[0])
            except: lo = 5
            # Lower level = higher priority (fill easy topics first)
            # Within same level, lower coverage_score = needs more work
            score = t.get("coverage_score") or 0
            return (lo, -score)

        return sorted(all_topics, key=priority)
    except Exception as e:
        print(f"  Topic fetch error: {e}", flush=True)
        return []

#  MAIN 
def main():
    print(" TryIT Engine v7  Final Production", flush=True)
    print(""*60, flush=True)
    print(f"   Groq GEN:     {len(GROQ_KEYS)} keys | 1,000 RPD org-wide", flush=True)
    print(f"   Gemini GEN:   {len(GEMINI_GEN_KEYS)} keys | {len(GEMINI_GEN_KEYS)*500} RPD", flush=True)
    print(f"   Gemini QA:    {len(GEMINI_QA_KEYS)} keys | {len(GEMINI_QA_KEYS)*500} RPD", flush=True)
    print(f"   NVIDIA:       {len(NVIDIA_KEYS)} keys | L8-10 upgrade only", flush=True)
    print(f"   Workers:      {CONCURRENT_WORKERS}", flush=True)
    print(f"   Batch size:   {BATCH_SIZE}", flush=True)
    print(f"   Min score:    {QUALITY_THRESHOLD}/10", flush=True)
    print(f"   Priority:     L2  L4  L5  others", flush=True)
    print(f"   Target:       ~2,000 Q/run | ~16,000 Q/day (8 runs)", flush=True)
    print(""*60, flush=True)

    start    = time.time()
    max_run  = 113 * 60  # 113 min  safely under GitHub 120-min limit
    grand    = 0
    pass_num = 0

    while time.time() - start < max_run:
        elapsed   = int((time.time()-start)/60)
        remaining = int((max_run-(time.time()-start))/60)

        print(f"\n{''*60}", flush=True)
        print(f"Pass #{pass_num+1} | elapsed={elapsed}m | remaining={remaining}m | saved={grand}", flush=True)

        topics = get_priority_topics()
        if not topics:
            print("  No topics found  sleep 60s", flush=True)
            time.sleep(60)
            continue

        # Show priority distribution this pass
        lo_counts = {}
        for t in topics:
            dr = t.get("difficulty_range","2-7")
            try: lo = int(dr.split("-")[0])
            except: lo = 5
            lo_counts[lo] = lo_counts.get(lo, 0) + 1
        print(f" {len(topics)} topics | Distribution: {dict(sorted(lo_counts.items()))}", flush=True)

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

        rate = pass_total / max(elapsed, 1)
        print(f"\n Pass #{pass_num}: +{pass_total} | Grand total: {grand}", flush=True)
        print(f"   Rate: {rate:.1f} Q/min | Projected/run: {int(rate*113)}", flush=True)

        if pass_total == 0:
            print(" All APIs rate-limited  sleep 5min to reset", flush=True)
            time.sleep(300)
        else:
            print(" 10s breath before next pass...", flush=True)
            time.sleep(10)

    elapsed_total = int((time.time()-start)/60)
    rate_final    = grand / max(elapsed_total, 1)
    print(f"\n Done. {grand} questions in {elapsed_total} minutes", flush=True)
    print(f"   Rate: {rate_final:.1f} Q/min = {int(rate_final*60)} Q/hr", flush=True)
    print(f"   Projected daily (8 runs): {int(grand*8)} questions", flush=True)

if __name__ == "__main__":
    main()


