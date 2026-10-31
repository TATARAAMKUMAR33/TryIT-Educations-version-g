"""
TryIT Question Engine v3 - ULTIMATE MULTI-PROVIDER
Loads 29 generation keys across 7 providers.
"""
import os
import os, json, time, uuid, re, itertools, random, threading
from entity_engine import get_context
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair
from key_pool import get_pool
from diagram_mapping import DIAGRAM_KIND_BY_TOPIC_ID
from svg_sanitizer import sanitize_question_svgs
# Note: Validators for biology/physics are structural for now, but they ensure no empty SVGs are saved.


load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ── LOAD ALL KEYS ──
def load_all_keys(prefix, max_n=6):
    keys = []
    old = os.getenv(prefix)
    if old and old.strip(): keys.append(old.strip())
    for i in range(1, max_n+1):
        k = os.getenv(f"{prefix}_{i}")
        if k and k.strip(): keys.append(k.strip())
    return keys

NVIDIA_KEYS = load_all_keys("NVIDIA_API_KEY", 5)
GROQ_KEYS = load_all_keys("GROQ_API_KEY", 5)
SAMBANOVA_KEYS = load_all_keys("SAMBANOVA_API_KEY", 5)
OPENROUTER_KEYS = load_all_keys("OPENROUTER_API_KEY", 5)
GH_MODELS_KEYS = load_all_keys("GH_MODELS_TOKEN", 5)
MISTRAL_KEYS = load_all_keys("MISTRAL_API_KEY", 5)
OPENAI_KEYS = load_all_keys("OPENAI_API_KEY", 5)
GEMINI_KEYS = load_all_keys("GEMINI_API_KEY", 6)

# ── BUILD CLIENTS & POOLS ──
NVIDIA_CLIENTS = [(k, OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k), "nvidia/nemotron-3-super-120b-a12b") for k in NVIDIA_KEYS]
GROQ_CLIENTS = [(k, OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k), "openai/gpt-oss-120b") for k in GROQ_KEYS]
SAMBANOVA_CLIENTS = [(k, OpenAI(base_url="https://api.sambanova.ai/v1", api_key=k), "Meta-Llama-3.3-70B-Instruct") for k in SAMBANOVA_KEYS]
OPENROUTER_CLIENTS = [(k, OpenAI(base_url="https://openrouter.ai/api/v1", api_key=k), "meta-llama/llama-3.3-70b-instruct:free") for k in OPENROUTER_KEYS]
GH_MODELS_CLIENTS = [(k, OpenAI(base_url="https://models.inference.ai.azure.com", api_key=k), "gpt-4o-mini") for k in GH_MODELS_KEYS]
MISTRAL_CLIENTS = [(k, OpenAI(base_url="https://api.mistral.ai/v1", api_key=k), "mistral-large-latest") for k in MISTRAL_KEYS]
OPENAI_CLIENTS = [(k, OpenAI(base_url="https://api.openai.com/v1", api_key=k), "gpt-4o-mini") for k in OPENAI_KEYS]

NVIDIA_POOL = get_pool("NVIDIA", NVIDIA_KEYS, cooldown_seconds=90)
GROQ_POOL = get_pool("Groq", GROQ_KEYS, cooldown_seconds=90)
SAMBANOVA_POOL = get_pool("SambaNova", SAMBANOVA_KEYS, cooldown_seconds=60)
OPENROUTER_POOL = get_pool("OpenRouter", OPENROUTER_KEYS, cooldown_seconds=90)
GH_MODELS_POOL = get_pool("GitHub", GH_MODELS_KEYS, cooldown_seconds=60)
MISTRAL_POOL = get_pool("Mistral", MISTRAL_KEYS, cooldown_seconds=60)
OPENAI_POOL = get_pool("OpenAI", OPENAI_KEYS, cooldown_seconds=60)

# ── GEMINI SETUP ──
GEMINI_MODEL = "gemini-2.5-flash"
def _find_working_gemini_model(key):
    client = genai.Client(api_key=key)
    for model in ["gemini-flash-lite-latest", "gemini-2.5-flash", "gemini-3.5-flash"]:
        try:
            client.models.generate_content(model=model, contents="hi")
            return model
        except Exception: continue
    return None

print("🔎 Verifying Gemini keys...", flush=True)
WORKING_GEMINI_KEYS = []
for i, k in enumerate(GEMINI_KEYS):
    model = _find_working_gemini_model(k)
    if model:
        WORKING_GEMINI_KEYS.append((k, model))
        print(f"  ✅ Gemini key {i+1} works with {model}", flush=True)

print(f"🔐 Using {len(WORKING_GEMINI_KEYS)} of {len(GEMINI_KEYS)} Gemini keys", flush=True)
GEMINI_KEYS_ONLY = [k for k, _ in WORKING_GEMINI_KEYS]
GEMINI_KEY_TO_MODEL = {k: m for k, m in WORKING_GEMINI_KEYS}
GEMINI_POOL = get_pool("Gemini", GEMINI_KEYS_ONLY, cooldown_seconds=120) if GEMINI_KEYS_ONLY else None

# ── CONFIG ──
BATCH_SIZE = 5
TARGET_L1_L5 = 200
TARGET_L6_L10 = 500
QUALITY_THRESHOLD = 9
CONCURRENT_WORKERS = 5

def get_dynamic_rules():
    context = get_context()
    return f"""
CRITICAL: Generate 100% ORIGINAL questions.
- Never reproduce, paraphrase, or reword any real exam question.
- {context}
- Do NOT use 'A, B, C' or generic variables. Use the names and locations provided above.
"""

_pattern_cache = {}
def get_pyq_context(topic_id):
    if topic_id in _pattern_cache: return _pattern_cache[topic_id]
    try:
        r = s.table('exam_syllabus_map').select('exam_id, weightage_percent').eq('topic_id', topic_id).execute()
        rows = r.data or []
    except Exception: rows = []
    if not rows:
        _pattern_cache[topic_id] = ("", []); return _pattern_cache[topic_id]
    exam_ids = sorted(set(x['exam_id'] for x in rows))
    pattern = f"EXAM PATTERN: Appears in {', '.join(exam_ids[:8])}"
    result = (pattern, exam_ids)
    _pattern_cache[topic_id] = result
    return result

def get_existing_count(topic_id, level):
    try:
        r = s.table('questions').select('id', count='exact').eq('topic_id', topic_id).eq('level', level).execute()
        return r.count or 0
    except Exception: return 0

def extract_json_array(text):
    if not text: return None
    text = re.sub(r'^```json\s*|\s*```$', '', text.strip(), flags=re.MULTILINE).strip()
    for cand in [text, text[text.find('['):text.rfind(']')+1] if '[' in text else text]:
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

def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags):
    pattern_str, _ = get_pyq_context(topic_id)
    diagram_kind = DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id)
    diagram_instruction = ""
    if diagram_kind:
        diagram_instruction = f'''
        THIS QUESTION REQUIRES A DIAGRAM: You must include a "diagram_svg" (or equivalent) field in your JSON output.
        Diagram Type Required: {diagram_kind}. Ensure the SVG is valid XML and matches the question logic.
        '''
    exam_str = ', '.join(exam_tags[:6]) if exam_tags else 'Indian competitive exams'
    prompt = f"""You are an expert MCQ writer for Indian competitive exams.
TOPIC: {topic_name}
SUBJECT: {subject_id}
DIFFICULTY LEVEL: {level}/10
TARGET EXAMS: {exam_str}
COUNT: {count} questions
{pattern_str}
{diagram_instruction}
{get_dynamic_rules()}

CRITICAL RULES:
1. DO NOT output your thought process, internal monologue, or self-corrections (e.g., never say 'Wait', 'Actually', 'Let me re-evaluate').
2. FIRST, solve the problem mathematically. THEN, construct the options so the correct answer is exactly among them.
3. The 'why_correct' field MUST ONLY contain the final, flawless mathematical logic.

Return ONLY raw JSON array. Start with [ end with ]. No thinking, no markdown.
Each object must have exactly these fields:
- question: The question text.
- options: Array of 4 strings.
- correct_answer: Integer (0-3).
- why_correct: Step-by-step logic for the correct answer.
- why_wrong_option_b: Explain the misconception that leads to option B.
- why_wrong_option_c: Explain the misconception that leads to option C.
- why_wrong_option_d: Explain the misconception that leads to option D.
- story_explanation: Create a RELATABLE, CONVERSATIONAL STORY using everyday Indian characters (e.g., Ramu, Priya, a local shopkeeper, a cricket team). Do NOT just explain the theory. Tell a quick anecdote where this concept naturally applies so a student remembers it forever.
- shortcut_tips: A real mnemonic or topper's trick to solve this in 10 seconds.
- cross_exam_intelligence: Name the SPECIFIC EXAMS this exact question type appears in (e.g., 'UPSC Prelims, SSC CGL Tier 1, RRB NTPC, State PSCs') and what angle they test. Do not give generic advice.
"""
    providers = [
        (NVIDIA_POOL, NVIDIA_CLIENTS), 
        (GROQ_POOL, GROQ_CLIENTS)
    ]
    random.shuffle(providers)
    
    for pool, clients in providers:
        if not clients: continue
        idx, key = pool.get_key(wait=False)
        if key is None: continue
        client_tuple = next((c for c in clients if c[0] == key), None)
        if not client_tuple: continue
        _, client, model = client_tuple
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "Output ONLY valid JSON arrays."}, {"role": "user", "content": prompt}],
                temperature=0.6, max_tokens=4000, timeout=60,
            )
            msg = resp.choices[0].message
            raw = msg.content or getattr(msg, 'reasoning_content', None) or ''
            if not raw: pool.mark_error(idx); continue
            data = extract_json_array(raw)
            if not data: pool.mark_error(idx); continue
            valid = [q for q in data if (isinstance(q, dict) and q.get('question') and isinstance(q.get('options'), list) and len(q['options']) == 4 and isinstance(q.get('correct_answer'), int) and 0 <= q['correct_answer'] <= 3)]
            if valid:
                pool.mark_success(idx)
                print(f'      ✅ {len(valid)}/{len(data)} via {pool.name.lower()}', flush=True)
                return valid
        except Exception as e:
            err = str(e)
            if '429' in err or 'rate' in err.lower() or 'timed out' in err.lower(): pool.mark_rate_limit(idx, cooldown=45)
            elif '401' in err or '403' in err: pool.mark_dead(idx, reason='invalid key')
            else: pool.mark_error(idx)
            continue
    return []

def verify(q, level):
    if not GEMINI_POOL: return True, 7, 'no verifier'
    idx, key = GEMINI_POOL.get_key(wait=True)
    if key is None: return True, 7, 'no verifier'
    model = GEMINI_KEY_TO_MODEL[key]
    try:
        client = genai.Client(api_key=key)
        prompt = f"""You are a strict math and logic examiner.
FIRST: Solve the problem independently.
SECOND: Check if the provided correct_answer index exactly matches your solved answer.
THIRD: Check if the explanation contains confused monologue (like 'Wait' or 'Actually').
Q: {q.get('question','')}
Options: {q.get('options',[])}
Provided correct index: {q.get('correct_answer',0)}
Provided Explanation: {q.get('why_correct','')}

Return ONLY JSON: {{"passed": true, "score": 9, "reason": "Math matches."}} OR {{"passed": false, "score": 0, "reason": "Math does not match / Monologue detected."}}"""
        r = client.models.generate_content(model=model, contents=prompt)
        txt = re.sub(r'^```json\s*|\s*```$', '', (r.text or '').strip(), flags=re.MULTILINE).strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if not m: GEMINI_POOL.mark_error(idx); return False, 0, 'no json'
        d = json_repair.loads(m.group())
        GEMINI_POOL.mark_success(idx)
        return d.get('passed', False), d.get('score', 0), d.get('reason', '')
    except Exception as e:
        err = str(e)
        if '429' in err or 'quota' in err.lower() or 'rate' in err.lower():
            GEMINI_POOL.mark_rate_limit(idx, cooldown=60)
        elif '401' in err or '403' in err:
            GEMINI_POOL.mark_dead(idx, reason='invalid key')
        else:
            GEMINI_POOL.mark_error(idx)
        return False, 0, err[:50]

def save(q, topic_id, subject_id, level, score, exam_tags):
    # Sanitize any SVGs if the topic requires a diagram
    diagram_kind = DIAGRAM_KIND_BY_TOPIC_ID.get(topic_id)
    if diagram_kind:
        q = sanitize_question_svgs(q, diagram_kind)
    rec = {
        "id": f"q_{uuid.uuid4().hex[:16]}", "topic_id": topic_id, "subject_id": subject_id, "level": level,
        "difficulty": "Easy" if level <= 3 else "Medium" if level <= 6 else "Hard" if level <= 8 else "Expert",
        "pattern_type": "standalone_mcq4", "question_en": q["question"], "options_en": q["options"],
        "correct_answer": q["correct_answer"],
        "explanation": {k: q.get(k, "") for k in ["why_correct", "why_wrong_option_b", "why_wrong_option_c", "why_wrong_option_d", "story_explanation", "shortcut_tips", "cross_exam_intelligence"]},
        "translations": {}, "exam_tags": exam_tags, "has_visual": False, "visual_type": None, "visual_data": None,
        "access_tier": "free" if level <= 6 else "pro", "copyright_original": True, "verified": True, "quality_score": score,
        "report_count": 0, "generated_by": "tryit_v3", "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try: s.table('questions').insert(rec).execute(); return True
    except Exception: return False

def process_topic_level(topic_id, topic_name, subject_id, level, target, exam_tags):
    existing = get_existing_count(topic_id, level)
    if existing >= target: return 0
    needed = target - existing
    print(f'   ⏳ {topic_id} L{level}: {existing}/{target} → need {needed}')
    saved = 0; empty_rounds = 0
    while saved < needed and empty_rounds < 3:
        qs = generate_batch(topic_id, topic_name, subject_id, level, min(BATCH_SIZE, needed - saved), exam_tags)
        if not qs: empty_rounds += 1; time.sleep(3); continue
        empty_rounds = 0
        for q in qs:
            ok, score, reason = verify(q, level)
            if ok and score >= QUALITY_THRESHOLD:
                if save(q, topic_id, subject_id, level, score, exam_tags):
                    saved += 1
                    print(f'      ✅ saved ({saved}/{needed}) score={score}')
        time.sleep(0.5)
    print(f'   🎉 {topic_id} L{level}: +{saved} saved')
    return saved

def process_topic(topic):
    tid = topic['topic_id']; tname = topic.get('topic_name', tid); sid = topic.get('subject_id') or 'general'
    dr = topic.get('difficulty_range') or '2-7'
    try: lo, hi = map(int, dr.split('-'))
    except: lo, hi = 2, 7
    try:
        exam_tags = sorted(set(r['exam_id'] for r in (s.table('exam_syllabus_map').select('exam_id').eq('topic_id', tid).execute().data or [])))
    except: exam_tags = []
    print(f'\n📘 {tid} [L{lo}-L{hi}] exams={exam_tags[:4]}')
    total = 0
    for lvl in range(lo, hi+1):
        total += process_topic_level(tid, tname, sid, lvl, TARGET_L1_L5 if lvl <= 5 else TARGET_L6_L10, exam_tags)
    return total

def main():
    topics = s.table('topics').select('topic_id, topic_name, subject_id, difficulty_range, coverage_score').eq('launch_phase', 'phase_1_now').order('coverage_score', desc=True).execute().data
    print(f'\n📚 {len(topics)} topics queued\n')
    grand_total = 0
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as ex:
        futures = {ex.submit(process_topic, t): t['topic_id'] for t in topics}
        for fut in as_completed(futures):
            try: grand_total += fut.result()
            except Exception as e: print(f"   !! {futures[fut]}: {e}")
    print(f'\n✅ DONE. Total new: {grand_total}')

if __name__ == "__main__":
    main()
