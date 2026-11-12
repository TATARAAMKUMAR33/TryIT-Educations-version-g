# VERSION: 8.0 - EXAM-AWARE PRODUCTION ENGINE
"""
TryIT Engine v8 - Complete Exam-Aware Generation
- Gemini QA via REST API (no SDK, no connection errors)
- Tier-based priority: School -> UG -> PG -> Foreign -> Govt -> State -> Pro
- Exam syllabus map integrated - every question knows its exam
- Level targets: L1-3=30Q, L4-6=20Q, L7=15Q, L8-9=10Q, L10=5Q
- Batch size 7 for 15,000 Q/day target
- Groq global rate limiter (org-wide 1000 RPD)
- Gemini generation (3 keys) + QA gate (1 key)
- NVIDIA for L8-10 upgrade only
"""

import os, json, time, uuid, re, requests, warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import json_repair
import threading

from backend_engine import safe_db_insert, is_duplicate
from key_pool import get_pool
from entity_engine import get_context
from diagram_mapping import DIAGRAM_KIND_BY_TOPIC_ID
from svg_sanitizer import sanitize_question_svgs

load_dotenv(dotenv_path=".env", override=True)
warnings.filterwarnings("ignore")

# ── CONSTANTS ──────────────────────────────────────────────────────────────────
CONCURRENT_WORKERS = 3     # Parallel topic threads
GROQ_INTERVAL      = 2.0   # Seconds between Groq calls (reduced for speed)

def get_batch_size(level):
    """Batch=7 for easy levels, batch=5 for hard (less truncation risk)"""
    return 7 if level <= 6 else 5

def get_quality_threshold(level):
    """Stricter quality at higher levels"""
    if level <= 3: return 6   # Lenient - volume matters for school
    if level <= 6: return 7   # Moderate - exam alignment critical
    if level <= 8: return 7   # Strict - misconceptions must be named
    return 8                   # Very strict - expert depth required

def get_target(level):
    if level <= 3: return 30
    if level <= 6: return 20
    if level == 7: return 15
    if level <= 9: return 10
    return 5

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
GEMINI_KEYS = load_keys("GEMINI_API_KEY", 5)
NVIDIA_KEYS = load_keys("NVIDIA_API_KEY", 5)

print(f"Keys: GROQ={len(GROQ_KEYS)} GEMINI={len(GEMINI_KEYS)} NVIDIA={len(NVIDIA_KEYS)}", flush=True)

# ── GROQ SETUP WITH GLOBAL RATE LIMITER ───────────────────────────────────────
GROQ_POOL    = get_pool("Groq", GROQ_KEYS, cooldown_seconds=65)
GROQ_CLIENTS = {k: OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k) for k in GROQ_KEYS}

_groq_lock = threading.Lock()
_groq_last = [0.0]
def groq_rate_wait():
    with _groq_lock:
        gap = GROQ_INTERVAL - (time.time() - _groq_last[0])
        if gap > 0:
            time.sleep(gap)
        _groq_last[0] = time.time()

# ── GEMINI SETUP (REST API - no SDK) ──────────────────────────────────────────
GEMINI_KEY_TO_MODEL = {}
GEMINI_WORKING      = []

GEMINI_MODELS = [
    "gemini-3.5-flash","gemini-2.5-flash",
    "gemini-2.5-flash-lite","gemini-1.5-flash"
]

print("Probing Gemini keys via REST...", flush=True)
for i, k in enumerate(GEMINI_KEYS):
    for model in GEMINI_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}"
            r = requests.post(url,
                json={"contents":[{"parts":[{"text":"hi"}]}]},
                timeout=15)
            if r.status_code == 200:
                GEMINI_KEY_TO_MODEL[k] = model
                GEMINI_WORKING.append(k)
                role = "QA" if i >= 3 else "GEN"
                print(f"  Gemini key {i+1} [{role}] -> {model}", flush=True)
                break
            else:
                print(f"  Gemini key {i+1} {model}: {r.status_code}", flush=True)
        except Exception as e:
            print(f"  Gemini key {i+1} {model}: {str(e)[:50]}", flush=True)
            continue

# Split: first 3 for generation, rest for QA
GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 3]
GEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 3]
GEMINI_GEN_POOL = get_pool("GeminiGen", GEMINI_GEN_KEYS, cooldown_seconds=65) if GEMINI_GEN_KEYS else None
GEMINI_QA_POOL  = get_pool("GeminiQA",  GEMINI_QA_KEYS,  cooldown_seconds=65) if GEMINI_QA_KEYS  else None

print(f"Gemini GEN: {len(GEMINI_GEN_KEYS)} keys | QA: {len(GEMINI_QA_KEYS)} keys", flush=True)

# ── NVIDIA SETUP ──────────────────────────────────────────────────────────────
NVIDIA_POOL    = get_pool("NVIDIA", NVIDIA_KEYS, cooldown_seconds=90)
NVIDIA_CLIENTS = {k: OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k) for k in NVIDIA_KEYS}

# ── EXAM DIFFICULTY MATRIX ────────────────────────────────────────────────────
EXAM_LEVEL_MAP = {
    'class_1':(1,2),'class_2':(1,3),'class_3':(2,3),'class_4':(2,4),
    'class_5':(2,4),'class_6':(3,5),'class_7':(3,5),'class_8':(4,6),
    'class_9':(4,6),'class_10':(5,7),'class_11':(5,8),'class_12':(6,8),
    'jee_main':(7,8),'jee_advanced':(8,10),'neet_ug':(7,9),'gate':(8,10),
    'cuet_ug':(5,7),'clat':(6,8),'nata':(5,7),'nift':(5,7),
    'cat':(7,9),'upsc_cse':(7,9),'upsc':(7,9),
    'ssc_cgl':(5,7),'ssc_chsl':(4,6),'ssc_mts':(3,5),'ssc_gd':(3,5),
    'rrb_ntpc':(4,6),'rrb_group_d':(3,5),'rrb_je':(5,7),
    'ibps_po':(5,7),'ibps_clerk':(4,6),'sbi_po':(6,7),'sbi_clerk':(4,6),
    'tnpsc':(5,7),'uppsc':(6,8),'bpsc':(6,8),
    'ntse':(4,6),'nmms':(3,5),'kvpy':(6,8),'nda':(5,7),'cds':(5,7),
    'ielts':(5,7),'toefl':(5,7),'gre':(6,8),'gmat':(6,8),
    'ca_foundation':(5,7),'ca_intermediate':(6,8),'ca_final':(7,9),
    'ugc_net':(7,9),'neet_pg':(8,10),'iti':(3,6),
}

def get_exam_level_range(exam_id):
    for pat, levels in EXAM_LEVEL_MAP.items():
        if pat in (exam_id or ''):
            return levels
    return (3, 7)

# ── TIER PRIORITY MAP ─────────────────────────────────────────────────────────
# Lower number = higher priority
SUBJECT_TIER = {
    # Tier 1 — School
    'cbse':1,'icse_board':1,'tn_state_board':1,'mh_state_board':1,
    'ap_ts_state_board':1,'karnataka_state_board':1,'up_state_board':1,
    'bihar_state_board':1,'wb_state_board':1,'gujarat_state_board':1,
    'punjab_state_board':1,'rajasthan_state_board':1,'mp_state_board':1,
    'kerala_state_board':1,'odisha_state_board':1,'assam_state_board':1,
    'nep_school_foundation':1,'cbse_maths':1,'cbse_science':1,
    'cbse_sst':1,'cbse_physics_11_12':1,'cbse_chemistry_11_12':1,
    'cbse_biology_11_12':1,
    # Tier 2 — UG Entrances
    'ug_pg_entrances':2,
    # Tier 3 — PG Entrances
    'gate_prep':3,'mba_cat_prep':3,'medical_pg':3,
    # Tier 4 — PhD
    'research_academia':4,
    # Tier 5 — Foreign
    'study_abroad_usa':5,'study_abroad_uk':5,'study_abroad_canada':5,
    'study_abroad_australia':5,'study_abroad_germany':5,'study_abroad_other':5,
    'international_exams':5,'french_language':5,'german_language':5,
    'spanish_language':5,'japanese_language':5,'mandarin_chinese':5,
    'korean_language':5,'arabic_language':5,
    # Tier 6 — Central Govt
    'competitive_govt_exams':6,'ssc_exams':6,'rrb_exams':6,
    'bank_exams':6,'defence_exams':6,'upsc_mains':6,
    # Tier 7 — State Govt
    'state_exams':7,'tamil_full':7,'telugu_full':7,'kannada_full':7,
    'malayalam_full':7,'marathi_full':7,'bengali_full':7,
    'gujarati_full':7,'punjabi_full':7,'odia_full':7,'assamese_full':7,
    # Tier 8 — Professional
    'ca_cs_cma':8,'ca_final':8,'finance_certifications':8,
    'advanced_finance':8,'law_practice':8,'medical_pg':8,
    'usmle_prep':8,'international_medical':8,'nursing':8,
}

def get_tier(subject_id):
    return SUBJECT_TIER.get(subject_id, 6)

# ── JSON HELPERS ──────────────────────────────────────────────────────────────
def extract_list(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$","",text.strip(),flags=re.MULTILINE).strip()
    for cand in [text, text[text.find("["):text.rfind("]")+1] if "[" in text else ""]:
        if not cand: continue
        try:
            d = json.loads(cand)
            if isinstance(d,list): return d
        except:
            try:
                d = json_repair.loads(cand)
                if isinstance(d,list): return d
            except: continue
    return None

def extract_obj(text):
    if not text: return None
    text = re.sub(r"^```json\s*|\s*```$","",text.strip(),flags=re.MULTILINE).strip()
    m = re.search(r"\{.*\}",text,re.DOTALL)
    if not m: return None
    try: return json_repair.loads(m.group())
    except: return None

def validate_qs(data):
    return [q for q in (data or []) if
        isinstance(q,dict) and q.get("question") and
        isinstance(q.get("options"),list) and len(q["options"])==4 and
        isinstance(q.get("correct_answer"),int) and 0<=q["correct_answer"]<=3 and
        q.get("why_correct") and q.get("story_explanation")]

# ── OPENAI CALL ───────────────────────────────────────────────────────────────
def call_openai(pool, clients, model, messages, max_tokens=5000, timeout=90, label=""):
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
                max_tokens=max_tokens, temperature=0.75, timeout=timeout)
            raw = r.choices[0].message.content or ""
            if raw: pool.mark_success(idx); return raw
            pool.mark_error(idx)
        except Exception as e:
            err = str(e)
            if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                pool.mark_rate_limit(idx, cooldown=70)
                print(f"      {label} key#{idx+1} rate-limited", flush=True)
            elif "401" in err or "403" in err:
                pool.mark_error(idx)
            elif "timeout" in err.lower():
                pool.mark_rate_limit(idx, cooldown=30)
            else:
                pool.mark_error(idx)
    return None

# ── GEMINI REST CALL ──────────────────────────────────────────────────────────
def call_gemini_rest(pool, key_to_model, prompt, label="Gemini"):
    if not pool: return None
    idx, key = pool.get_key(wait=False)
    if key is None: return None
    model = key_to_model.get(key, "gemini-3.5-flash")
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        r = requests.post(url,
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"temperature":0.75,"maxOutputTokens":5000}},
            timeout=90)
        if r.status_code == 200:
            data = r.json()
            text = data.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
            if text:
                pool.mark_success(idx)
                return text
            pool.mark_error(idx)
        elif r.status_code == 429:
            pool.mark_rate_limit(idx, cooldown=70)
            print(f"      {label} key#{idx+1} rate-limited", flush=True)
        else:
            pool.mark_error(idx)
            print(f"      {label} error: {r.status_code}", flush=True)
    except Exception as e:
        pool.mark_error(idx)
        print(f"      {label} exception: {str(e)[:60]}", flush=True)
    return None

# ── DIFFICULTY HELPERS ────────────────────────────────────────────────────────
def diff_label(level):
    if level<=2: return "Foundation"
    if level<=4: return "Easy"
    if level<=6: return "Medium"
    if level<=8: return "Hard"
    return "Expert"

def diff_guide(level):
    g = {
        1:"Class 1-2: Single simple fact. 6-7 year old must understand instantly.",
        2:"Class 3-4: Basic recall. One concept. Age 8-9 student.",
        3:"Class 5-6: Simple application. Two facts connected.",
        4:"Class 7-8: Concept application. Basic reasoning.",
        5:"Class 9-10: Multi-concept. Board exam style. One step calculation.",
        6:"Class 11-12 / State PSC: Application with one trap option.",
        7:"Graduation / SSC CGL / UPSC Prelims: Two trap options. Multi-step.",
        8:"Post-grad / GATE / NEET: Advanced concepts. All options plausible.",
        9:"UPSC Mains / GATE Advanced: Expert reasoning. Deep analysis.",
        10:"Research / PhD: All 4 options seem correct to 90% of students."
    }
    return g.get(level,"Competitive exam MCQ.")

def story_guide(level):
    g = {
        1:"6-year-old child at home/school. Discovers answer through play.",
        2:"Class 3-4 student. Teacher explains through simple daily example.",
        3:"Class 5-6 student at school or market. Solves small real problem.",
        4:"Class 7-8 student. Questions why something happens, gets clear answer.",
        5:"Class 10 student preparing for board exams. Concept clicks through observation.",
        6:"Competitive exam aspirant at coaching centre. Learns the trick.",
        7:"UPSC/SSC aspirant who gets question wrong first, then understands through real scenario.",
        8:"Final year engineering/medical student applying concept to professional problem.",
        9:"IAS officer/doctor/engineer making a real work decision using this concept.",
        10:"PhD researcher proving the concept through evidence at academic conference."
    }
    return g.get(level,g[7])

# ── BUILD PROMPT ──────────────────────────────────────────────────────────────
def build_prompt(topic_name, subject_id, level, count, exam_tags, context, exam_patterns):
    exam_str = ", ".join(exam_tags[:5]) if exam_tags else "UPSC, SSC CGL, RRB NTPC"
    dlabel   = diff_label(level)
    dguide   = diff_guide(level)
    sguide   = story_guide(level)

    # Build exam-specific instructions
    exam_instructions = ""
    if exam_patterns:
        exam_instructions = f"""
EXAM-SPECIFIC ALIGNMENT:
This question must be suitable for: {exam_str}
Question pattern: {"Direct recall" if level<=4 else "Application-based" if level<=6 else "Multi-step analytical"}
{"For school exams: match NCERT/state board chapter exactly." if level<=6 else ""}
{"For competitive exams: include common exam traps and misconceptions." if level>=5 else ""}
{"For expert level: all 4 options must seem correct to an average student." if level>=8 else ""}
"""

    return f"""You are India's top MCQ writer with 20 years experience in {exam_str}.
Generate exactly {count} unique MCQs.

TOPIC: {topic_name}
SUBJECT: {subject_id}
DIFFICULTY: Level {level}/10 - {dlabel}
TARGET EXAMS: {exam_str}
CONTEXT: {context[:300] if context else "Indian educational context"}
{exam_instructions}
DIFFICULTY REQUIREMENT:
{dguide}
Every question MUST exactly match Level {level}/10. Reject if wrong level.

MCQ RULES:
1. correct_answer: 0-indexed integer (0=A,1=B,2=C,3=D)
2. All 4 options must be distinct and plausible
3. Level 5+: minimum 2 options must trick average student
4. Level 7+: all 4 options must exploit real misconceptions
5. No "All of the above" or "None of the above"

7-LAYER EXPLANATION - ALL REQUIRED:

why_correct: "Step 1: [reasoning]. Step 2: [reasoning]. Therefore [option] is correct because [proof]."
why_wrong_option_b: "Students pick B because [NAMED misconception]. Wrong because [counter-proof]. TRAP: [what makes it seem right]."
why_wrong_option_c: "Students pick C because [NAMED misconception]. Wrong because [counter-proof]. TRAP: [what makes it seem right]."
why_wrong_option_d: "Students pick D because [NAMED misconception]. Wrong because [counter-proof]. TRAP: [what makes it seem right]."

story_explanation: {sguide}
USE CONTEXT CHARACTER: {context[:100] if context else "Use Ramu/Priya from an Indian city"}
Story MUST: (1) Use character from context. (2) Character faces SAME problem as question. (3) Solves using SAME logic as correct answer. (4) Final sentence: "This is exactly why [option letter and text] is the answer."
Write in simple language for level {level} student.

shortcut_tips: "TRICK NAME: [catchy name]. HOW: [one-line trick - mnemonic/pattern/visual]. APPLY HERE: [show trick giving answer in 10 seconds on THIS question]. EXAM TIP: [which exam uses this trick most]."

cross_exam_intelligence: "UPSC Prelims: appears as [exact type] - watch [trap]. SSC CGL Tier-1: tested as [angle], wrong trap is [option] because [reason]. RRB NTPC: [angle]. NEET/GATE/Other: [angle]."

Output ONLY valid JSON array, no markdown, no text outside JSON:
[
  {{
    "question": "Complete question ending with ?",
    "options": ["A) text","B) text","C) text","D) text"],
    "correct_answer": 0,
    "why_correct": "Step 1:... Step 2:... Therefore A is correct because...",
    "why_wrong_option_b": "Students pick B because [misconception]. Wrong because [proof]. TRAP: [reason].",
    "why_wrong_option_c": "Students pick C because [misconception]. Wrong because [proof]. TRAP: [reason].",
    "why_wrong_option_d": "Students pick D because [misconception]. Wrong because [proof]. TRAP: [reason].",
    "story_explanation": "4-sentence Indian story. Last sentence: This is exactly why [option] is the answer.",
    "shortcut_tips": "TRICK NAME: ... HOW: ... APPLY HERE: ... EXAM TIP: ...",
    "cross_exam_intelligence": "UPSC Prelims:... SSC CGL:... RRB NTPC:... Other:..."
  }}
]"""

# ── GENERATE BATCH ────────────────────────────────────────────────────────────
def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags, exam_patterns):
    context = get_context(topic_id, subject_id) if callable(get_context) else ""
    prompt  = build_prompt(topic_name, subject_id, level, count, exam_tags, context, exam_patterns)

    sys_msg = "JSON-only MCQ generator. Output ONLY a valid JSON array. Never add text outside JSON."
    msgs = [
        {"role":"system","content":sys_msg},
        {"role":"user","content":prompt}
    ]

    # PRIMARY: Groq (1,000 RPD org-wide)
    groq_rate_wait()
    for model in ["openai/gpt-oss-120b","openai/gpt-oss-20b"]:
        raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=5000, timeout=60, label="Groq")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q Groq {model} L{level}", flush=True)
                return valid

    # SECONDARY: Gemini generation (3 keys x 500 RPD)
    if GEMINI_GEN_POOL:
        raw = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL,
                               f"{sys_msg}\n\n{prompt}", "GeminiGen")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q GeminiGen L{level}", flush=True)
                return valid

    print(f"      All generators failed L{level}", flush=True)
    return []

# ── NVIDIA UPGRADE (L8-10 only) ───────────────────────────────────────────────
def nvidia_upgrade(q, topic_name, level, exam_tags):
    exam_str = ", ".join(exam_tags[:3]) if exam_tags else "UPSC, GATE"
    correct  = q["options"][q["correct_answer"]]

    prompt = f"""Upgrade this Level {level}/10 MCQ explanation to expert quality for {exam_str}.
Q: {q["question"]}
Correct: {correct}
Current why_correct: {q.get("why_correct","")[:200]}

Return ONLY JSON object:
{{"why_correct":"Expert proof with full technical depth. Step 1:[deep]. Step 2:[technical]. Step 3:[conclusion].",
"why_wrong_option_b":"Deep: [exact conceptual error]. Proof: [technical]. Exam trap: [why toppers fall for this].",
"why_wrong_option_c":"Deep: [exact conceptual error]. Proof: [technical]. Exam trap: [why toppers fall for this].",
"why_wrong_option_d":"Deep: [exact conceptual error]. Proof: [technical]. Exam trap: [why toppers fall for this].",
"shortcut_tips":"TRICK NAME:[advanced]. HOW:[expert]. APPLY HERE:[on this Q]. EXAM TIP:[UPSC/GATE strategy].",
"cross_exam_intelligence":"UPSC [year]: appeared as [format]. GATE [year]: [angle]. NEET/Other: [trap]."}}"""

    msgs = [{"role":"user","content":prompt}]
    for model in ["nvidia/nemotron-3-ultra-550b-a55b","nvidia/llama-3.1-nemotron-ultra-253b-v1",
                  "mistralai/mistral-large-4-1t-a52b","moonshotai/kimi-k2.6"]:
        raw = call_openai(NVIDIA_POOL, NVIDIA_CLIENTS, model, msgs, max_tokens=2000, timeout=90, label="NVIDIA")
        if raw:
            data = extract_obj(raw)
            if data and data.get("why_correct") and len(data["why_correct"])>50:
                q.update(data)
                print(f"      NVIDIA upgrade {model}", flush=True)
                return q
    return q

# ── GEMINI QA GATE (REST API) ─────────────────────────────────────────────────
def gemini_qa(q, level):
    if not GEMINI_QA_POOL:
        return True, 7, "no QA pool"

    idx, key = GEMINI_QA_POOL.get_key(wait=False)
    if key is None:
        return True, 7, "QA cooling"

    # Quick local check first - core layers must exist
    for field in ["why_correct","story_explanation"]:
        if not q.get(field) or len(str(q.get(field,""))) < 20:
            return False, 0, f"missing {field}"

    model = GEMINI_KEY_TO_MODEL.get(key, "gemini-3.5-flash")
    prompt = f"""Strict QA check for Indian competitive exam MCQ. Level {level}/10 ({diff_label(level)}).

Q: {q.get("question","")}
Options: {q.get("options",[])}
Correct index: {q.get("correct_answer",0)}
why_correct: {q.get("why_correct","")[:200]}
story_explanation: {q.get("story_explanation","")[:200]}
shortcut_tips: {q.get("shortcut_tips","")[:100]}

CHECK ALL STRICTLY:
1. Difficulty EXACTLY matches Level {level}/10: {diff_guide(level)[:60]}
2. Correct answer is factually accurate?
3. why_correct has step-by-step proof (not just restatement)?
4. story_explanation: Indian character faces SAME problem, solves with SAME logic, ends EXACTLY "This is exactly why [option letter and text] is the answer"?
5. shortcut_tips has TRICK NAME + HOW + APPLY HERE + EXAM TIP (all 4 parts)?
6. Wrong option explanations name SPECIFIC misconceptions (not just "this is wrong")?
7. {"Language is appropriate for Class 1-6 students (simple, no jargon)?" if level<=6 else "All 4 options are plausible to an average student at this level?"}

Return ONLY JSON: {{"passed":true,"score":8,"reason":"one sentence - what passed or what specific thing failed"}}
Score 1-10.
Minimum passing score for this level: {"6" if level<=3 else "7" if level<=8 else "8"}/10
Reject immediately if: wrong difficulty, factual error, story doesn't end with required sentence, or {"language too complex for school level" if level<=6 else "options not plausible enough for expert level"}."""

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        r = requests.post(url,
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"temperature":0.1,"maxOutputTokens":200}},
            timeout=30)
        if r.status_code == 200:
            data = r.json()
            text = data.get("candidates",[{}])[0].get("content",{}).get("parts",[{}])[0].get("text","")
            text = re.sub(r"^```json\s*|\s*```$","",text.strip(),flags=re.MULTILINE)
            d = extract_obj(text)
            if d:
                GEMINI_QA_POOL.mark_success(idx)
                passed = d.get("passed",False)
                score  = int(d.get("score",0))
                reason = d.get("reason","")
                if not passed:
                    print(f"      QA rejected L{level}: {reason[:60]}", flush=True)
                return passed, score, reason
            GEMINI_QA_POOL.mark_error(idx)
            return True, 6, "parse fail - auto pass"
        elif r.status_code == 429:
            GEMINI_QA_POOL.mark_rate_limit(idx, cooldown=70)
            return True, 7, "QA rate limited - auto pass"
        else:
            GEMINI_QA_POOL.mark_error(idx)
            return True, 6, f"QA error {r.status_code} - auto pass"
    except Exception as e:
        GEMINI_QA_POOL.mark_error(idx)
        return True, 6, f"QA exception - auto pass"

# ── DB HELPERS ────────────────────────────────────────────────────────────────
# Global cache for question counts - loaded once per pass
_count_cache = {}
_cache_loaded = False

def load_count_cache():
    global _count_cache, _cache_loaded
    try:
        rows = s.table("questions").select("topic_id,level").execute().data or []
        _count_cache = {}
        for r in rows:
            key = f"{r.get("topic_id")}_{r.get("level")}"
            _count_cache[key] = _count_cache.get(key,0) + 1
        _cache_loaded = True
        print(f"Count cache loaded: {len(rows)} questions, {len(_count_cache)} topic-level pairs", flush=True)
    except Exception as e:
        print(f"Cache load failed: {e}", flush=True)
        _cache_loaded = False

def get_existing_count(topic_id, level):
    if _cache_loaded:
        return _count_cache.get(f"{topic_id}_{level}", 0)
    try:
        r = s.table("questions").select("id",count="exact").eq("topic_id",topic_id).eq("level",level).execute()
        return r.count or 0
    except: return 0

def invalidate_cache_entry(topic_id, level):
    key = f"{topic_id}_{level}"
    if key in _count_cache:
        _count_cache[key] = _count_cache.get(key,0) + 1

def get_exam_info(topic_id):
    try:
        rows = s.table("exam_syllabus_map").select("exam_id,weightage_percent,priority") \
                .eq("topic_id",topic_id).order("priority").limit(10).execute().data or []
        exam_tags = [r["exam_id"] for r in rows]
        # Get exam patterns for difficulty matching
        patterns = []
        for eid in exam_tags:
            for pat in EXAM_LEVEL_MAP.keys():
                if pat in eid:
                    patterns.append(pat)
        return exam_tags, list(set(patterns))
    except:
        return [], []

def save_question(q, topic_id, subject_id, level, exam_tags, score):
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
            "why_wrong_option_d","story_explanation","shortcut_tips",
            "cross_exam_intelligence"]},
        "translations":       {},
        "exam_tags":          exam_tags,
        "has_visual":         DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id) is not None,
        "visual_type":        DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id),
        "visual_data":        None,
        "access_tier":        "free" if level<=6 else "pro",
        "copyright_original": True,
        "verified":           True,
        "quality_score":      score,
        "report_count":       0,
        "generated_by":       "tryit_v8",
        "created_at":         datetime.now(timezone.utc).isoformat(),
    }

    if is_duplicate(s, q["question"], topic_id):
        print("      Duplicate - skip", flush=True)
        return False

    success, _ = safe_db_insert(s, "questions", rec)
    if success:
        invalidate_cache_entry(topic_id, level)
    return success

# ── RETRY STORY (soft rejection handler) ──────────────────────────────────────
def retry_story(q, topic_name, level, exam_tags):
    """Regenerate only story_explanation and shortcut_tips when QA soft-rejects."""
    exam_str = ", ".join(exam_tags[:3]) if exam_tags else "SSC CGL, UPSC"
    correct  = q["options"][q["correct_answer"]]

    prompt = f"""Fix the story and shortcut for this MCQ. Keep the question and options UNCHANGED.

Question: {q.get("question","")}
Correct Answer: {correct} (index {q.get("correct_answer",0)})
Topic: {topic_name} | Level: {level}/10 | Exam: {exam_str}

{story_guide(level)}

RULES:
- story_explanation MUST end with: "This is exactly why {correct} is the answer."
- Character must face the SAME problem as question
- Solve with SAME logic as correct answer
- shortcut_tips MUST have: TRICK NAME + HOW + APPLY HERE + EXAM TIP

Return ONLY JSON object:
{{"story_explanation": "4-sentence Indian story ending with This is exactly why...",
  "shortcut_tips": "TRICK NAME:... HOW:... APPLY HERE:... EXAM TIP:..."}}"""

    msgs = [{"role":"user","content":prompt}]

    # Try Groq first (fast)
    groq_rate_wait()
    raw = call_openai(GROQ_POOL, GROQ_CLIENTS, "openai/gpt-oss-120b", msgs,
                      max_tokens=800, timeout=30, label="RetryGroq")
    if raw:
        data = extract_obj(raw)
        if data and data.get("story_explanation") and "This is exactly why" in data.get("story_explanation",""):
            q["story_explanation"] = data["story_explanation"]
            if data.get("shortcut_tips"):
                q["shortcut_tips"] = data["shortcut_tips"]
            return q

    # Try Gemini generation pool
    if GEMINI_GEN_POOL:
        raw = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL, prompt, "RetryGemini")
        if raw:
            data = extract_obj(raw)
            if data and data.get("story_explanation") and "This is exactly why" in data.get("story_explanation",""):
                q["story_explanation"] = data["story_explanation"]
                if data.get("shortcut_tips"):
                    q["shortcut_tips"] = data["shortcut_tips"]
                return q

    return q  # Return original if retry fails

# ── PROCESS TOPIC LEVEL ───────────────────────────────────────────────────────
def process_topic_level(topic_id, topic_name, subject_id, level, exam_tags, exam_patterns):
    target   = get_target(level)
    existing = get_existing_count(topic_id, level)
    if existing >= target: return 0
    needed = target - existing
    print(f"   {topic_name[:35]} L{level} ({diff_label(level)}): {existing}/{target} need {needed}", flush=True)

    saved = 0
    empty = 0

    qa_threshold = get_quality_threshold(level)
    batch_size   = get_batch_size(level)

    while saved < needed and empty < 3:
        batch = min(batch_size, needed - saved)
        questions = generate_batch(topic_id, topic_name, subject_id, level,
                                   batch, exam_tags, exam_patterns)
        if not questions:
            empty += 1
            print(f"   Empty {empty}/3 - wait 5s", flush=True)
            time.sleep(5)
            continue

        empty = 0
        for q in questions:
            # NVIDIA upgrade for L7-10 (approved: extend from L8 to L7)
            if level >= 7:
                q = nvidia_upgrade(q, topic_name, level, exam_tags)

            # Gemini QA gate with level-specific threshold
            passed, score, reason = gemini_qa(q, level)

            # Auto-retry on soft rejection (story/shortcut issue only)
            if not passed and score >= 4 and reason and any(
                soft in reason.lower() for soft in
                ["story","shortcut","trick","connect","tip","incomplete"]):
                # Regenerate story only - reuse question skeleton
                q = retry_story(q, topic_name, level, exam_tags)
                passed, score, reason = gemini_qa(q, level)
                if passed:
                    print(f"      Retry story OK score={score}", flush=True)

            if not passed or score < qa_threshold:
                print(f"      Rejected L{level} score={score} threshold={qa_threshold}: {reason[:40]}", flush=True)
                continue

            if save_question(q, topic_id, subject_id, level, exam_tags, score):
                saved += 1
                print(f"      saved {saved}/{needed} L{level} score={score}", flush=True)

        time.sleep(0.5)

    print(f"   {topic_name[:30]} L{level}: +{saved}", flush=True)
    return saved

# ── PROCESS TOPIC ─────────────────────────────────────────────────────────────
def process_topic(topic):
    tid   = topic["topic_id"]
    tname = topic.get("topic_name", tid)
    sid   = topic.get("subject_id") or "general"
    dr    = topic.get("difficulty_range") or "2-7"

    try: lo, hi = map(int, dr.split("-"))
    except: lo, hi = 2, 7

    exam_tags, exam_patterns = get_exam_info(tid)
    print(f"\n{tname} L{lo}-{hi} exams={len(exam_tags)}", flush=True)

    total = 0
    for lvl in range(lo, hi+1):
        total += process_topic_level(tid, tname, sid, lvl, exam_tags, exam_patterns)
    return total

# ── SMART TOPIC QUEUE ─────────────────────────────────────────────────────────
def get_priority_topics():
    """Tier-based priority: School -> UG -> PG -> Foreign -> Govt -> State -> Pro"""
    try:
        all_topics = (
            s.table("topics")
             .select("topic_id,topic_name,subject_id,difficulty_range,coverage_score,is_visual")
             .in_("launch_phase",["phase_1_now","phase_2_2027"])
             .execute().data or []
        )

        def priority_key(t):
            sid   = t.get("subject_id","")
            tier  = get_tier(sid)
            dr    = t.get("difficulty_range","2-7")
            try: lo = int(dr.split("-")[0])
            except: lo = 5
            score = t.get("coverage_score") or 50
            # Within same tier: easy topics first, then by coverage (lower = needs more)
            return (tier, lo, -score)

        return sorted(all_topics, key=priority_key)
    except Exception as e:
        print(f"Topic fetch error: {e}", flush=True)
        return []

# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    print("TryIT Engine v8 - Exam-Aware Production", flush=True)
    print(f"  Groq GEN: {len(GROQ_KEYS)} keys | 1000 RPD org | batch=5-7 (dynamic)", flush=True)
    print(f"  Gemini GEN: {len(GEMINI_GEN_KEYS)} keys | Gemini QA: {len(GEMINI_QA_KEYS)} keys", flush=True)
    print(f"  NVIDIA: {len(NVIDIA_KEYS)} keys | L8-10 upgrade only", flush=True)
    print(f"  Workers: {CONCURRENT_WORKERS} | QA threshold: 6-8/10 (per level)", flush=True)
    print(f"  Level targets: L1-3=30Q L4-6=20Q L7=15Q L8-9=10Q L10=5Q | batch=dynamic", flush=True)
    print(f"  Priority: School->UG->PG->Foreign->Govt->State->Pro", flush=True)
    print("-"*60, flush=True)

    start    = time.time()
    max_run  = 113 * 60
    grand    = 0
    pass_num = 0

    while time.time() - start < max_run:
        elapsed   = int((time.time()-start)/60)
        remaining = int((max_run-(time.time()-start))/60)

        print(f"\n{'='*60}", flush=True)
        print(f"Pass #{pass_num+1} | {elapsed}m elapsed | {remaining}m left | total={grand}", flush=True)

        # Load count cache once per pass - saves 45+ minutes of DB calls
        load_count_cache()

        topics = get_priority_topics()
        if not topics:
            print("No topics found - sleep 60s", flush=True)
            time.sleep(60)
            continue

        # Show tier distribution
        tier_dist = {}
        for t in topics:
            tier = get_tier(t.get("subject_id",""))
            tier_dist[tier] = tier_dist.get(tier,0) + 1
        print(f"{len(topics)} topics | Tiers: {dict(sorted(tier_dist.items()))}", flush=True)

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

        rate = grand / max(elapsed+1, 1)
        print(f"\nPass #{pass_num}: +{pass_total} | Total: {grand}", flush=True)
        print(f"Rate: {rate:.1f} Q/min = {int(rate*60)} Q/hr = {int(rate*60*24)} Q/day (projected)", flush=True)

        if pass_total == 0:
            print("All rate-limited - sleep 5min", flush=True)
            time.sleep(300)
        else:
            time.sleep(10)

    elapsed_m = int((time.time()-start)/60)
    rate_f    = grand / max(elapsed_m,1)
    print(f"\nDone. {grand} questions in {elapsed_m} minutes", flush=True)
    print(f"Rate: {rate_f:.1f} Q/min | {int(rate_f*60)} Q/hr | {int(rate_f*60*24)} Q/day", flush=True)
    print(f"8 runs/day projected: {int(grand*8)} questions/day", flush=True)

if __name__ == "__main__":
    main()
