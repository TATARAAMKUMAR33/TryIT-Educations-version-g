"""
TryIT Question Engine v2
- 5 NVIDIA + 5 Groq + 3 Cerebras = 13 generation keys rotating
- 5 Gemini keys for verification
- PYQ-matched via exam_syllabus_map
- Auto-resume, auto-save, auto-scale
- Target: 10,000 verified questions/day
"""
import os, json, time, uuid, re, itertools, random, threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair
from key_pool import get_pool

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ── LOAD ALL KEYS ──
def load_keys(prefix, max_n=5):
    keys = []
    for i in range(1, max_n+1):
        k = os.getenv(f"{prefix}_{i}")
        if k and k.strip(): keys.append(k.strip())
    return keys

NVIDIA_KEYS = load_keys("NVIDIA_API_KEY", 5)
GROQ_KEYS = load_keys("GROQ_API_KEY", 5)
# CEREBRAS removed (payment required)
GEMINI_KEYS = []
# Load un-suffixed (if exists)
_g = os.getenv("GEMINI_API_KEY")
if _g and _g.strip(): GEMINI_KEYS.append(_g.strip())
# Load suffixed _1 through _6
for i in range(1, 7):
    _k = os.getenv(f"GEMINI_API_KEY_{i}")
    if _k and _k.strip(): GEMINI_KEYS.append(_k.strip())
# Load GOOGLE_API_KEY (yesterday's un-suffixed working key)
_gg = os.getenv("GOOGLE_API_KEY")
if _gg and _gg.strip() and _gg.strip() not in GEMINI_KEYS:
    GEMINI_KEYS.append(_gg.strip())

# ── PROVIDER POOLS ──
# Build OpenAI clients once per key (reuse across requests)
NVIDIA_CLIENTS = [(k, OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k), "nvidia/nemotron-3-super-120b-a12b") for k in NVIDIA_KEYS]
GROQ_CLIENTS = [(k, OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k), "openai/gpt-oss-120b") for k in GROQ_KEYS]

# Key pools for intelligent rotation
NVIDIA_POOL = get_pool("NVIDIA", NVIDIA_KEYS, cooldown_seconds=90)
GROQ_POOL = get_pool("Groq", GROQ_KEYS, cooldown_seconds=90)

GEN_PROVIDERS = []  # kept for backwards-compat with verify_via_groq
for k in NVIDIA_KEYS:
    GEN_PROVIDERS.append(("nvidia", OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=k), "nvidia/nemotron-3-super-120b-a12b"))
for k in GROQ_KEYS:
    GEN_PROVIDERS.append(("groq", OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k), "openai/gpt-oss-120b"))
# Cerebras provider removed

print(f"🔌 Generation providers: NVIDIA×{len(NVIDIA_KEYS)}, Groq×{len(GROQ_KEYS)} = {len(GEN_PROVIDERS)} total")
print(f"🔐 Verification: Gemini×{len(GEMINI_KEYS)}")

# Models to try per key (in order)
GEMINI_MODELS_TO_TRY = [
    "gemini-flash-lite-latest",
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]

def _find_working_gemini_model(key):
    """Test a key against multiple models and return the first one that works."""
    client = genai.Client(api_key=key)
    for model in GEMINI_MODELS_TO_TRY:
        try:
            client.models.generate_content(model=model, contents="hi")
            return model
        except Exception:
            continue
    return None

print("🔎 Verifying Gemini keys on startup...", flush=True)
WORKING_GEMINI_KEYS = []           # list of (key, model) tuples
for i, k in enumerate(GEMINI_KEYS):
    model = _find_working_gemini_model(k)
    if model:
        WORKING_GEMINI_KEYS.append((k, model))
        print(f"  ✅ Gemini key {i+1} works with {model}", flush=True)
    else:
        print(f"  ❌ Gemini key {i+1} broken — skipping", flush=True)

print(f"🔐 Using {len(WORKING_GEMINI_KEYS)} of {len(GEMINI_KEYS)} Gemini keys", flush=True)
# Gemini key pool with cooldowns (60s cooldown on rate limit)
# WORKING_GEMINI_KEYS is a list of (key, model) tuples
GEMINI_KEYS_ONLY = [k for k, _ in WORKING_GEMINI_KEYS]
GEMINI_KEY_TO_MODEL = {k: m for k, m in WORKING_GEMINI_KEYS}
GEMINI_POOL = get_pool("Gemini", GEMINI_KEYS_ONLY, cooldown_seconds=120) if GEMINI_KEYS_ONLY else None
gemini_lock = threading.Lock()

# ── CONFIG (10K/day target) ──
BATCH_SIZE = 5
TARGET_L1_L5 = 200       # start here, scale to 1000 later
TARGET_L6_L10 = 500      # start here, scale to 5000 later
QUALITY_THRESHOLD = 9
MAX_TOPICS = None        # process all 215
CONCURRENT_WORKERS = 5   # 3x parallel topics

# ── COPYRIGHT SAFETY ──
COPYRIGHT_RULES = """
CRITICAL: Generate 100% ORIGINAL questions.
- Never reproduce, paraphrase, or reword any real exam question.
- Use completely new scenarios, numbers, names, settings.
- Inspired by pattern: OK. Same question with different numbers: NOT OK.
"""

# ── PYQ PATTERN LOOKUP ──
_pattern_cache = {}
def get_pyq_context(topic_id):
    if topic_id in _pattern_cache:
        return _pattern_cache[topic_id]
    try:
        r = s.table('exam_syllabus_map').select('exam_id, weightage_percent').eq('topic_id', topic_id).execute()
        rows = r.data or []
    except Exception:
        rows = []
    if not rows:
        _pattern_cache[topic_id] = ("", [])
        return _pattern_cache[topic_id]
    exam_ids = sorted(set(x['exam_id'] for x in rows))
    weights = [x['weightage_percent'] for x in rows if x['weightage_percent']]
    avg = sum(weights) / len(weights) if weights else 0
    pattern = f"""
EXAM PATTERN (from real exam data):
- Appears in: {', '.join(exam_ids[:8])}
- Avg weightage: {avg:.2f}%
- Match the STYLE and DIFFICULTY of these exams"""
    result = (pattern, exam_ids)
    _pattern_cache[topic_id] = result
    return result

def get_existing_count(topic_id, level):
    try:
        r = s.table('questions').select('id', count='exact').eq('topic_id', topic_id).eq('level', level).execute()
        return r.count or 0
    except Exception:
        return 0

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
            except Exception:
                continue
    return None

def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags):
    pattern_str, _ = get_pyq_context(topic_id)
    exam_str = ', '.join(exam_tags[:6]) if exam_tags else 'Indian competitive exams'
    prompt = f"""You are an expert MCQ writer for Indian competitive exams.

TOPIC: {topic_name}
SUBJECT: {subject_id}
DIFFICULTY LEVEL: {level}/10
TARGET EXAMS: {exam_str}
COUNT: {count} questions
{pattern_str}

{COPYRIGHT_RULES}

Generate {count} ORIGINAL MCQs. Each has exactly 4 options, 1 correct.

Return ONLY raw JSON array. Start with [ end with ]. No thinking, no markdown.
Each object has: question, options (4 strings), correct_answer (0-3),
why_correct, why_wrong_option_b, why_wrong_option_c, why_wrong_option_d,
story_explanation, shortcut_tips, cross_exam_intelligence
"""
    # Try NVIDIA first, then Groq — via pools
    for pool, clients in [(NVIDIA_POOL, NVIDIA_CLIENTS), (GROQ_POOL, GROQ_CLIENTS)]:
        if not clients:
            continue
        idx, key = pool.get_key(wait=False)
        if key is None:
            continue  # all keys in cooldown — try next provider
        # Find matching client
        client_tuple = next((c for c in clients if c[0] == key), None)
        if not client_tuple:
            continue
        _, client, model = client_tuple
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Output ONLY valid JSON arrays. No markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6, max_tokens=4000, timeout=60,
            )
            msg = resp.choices[0].message
            raw = msg.content or getattr(msg, 'reasoning_content', None) or ''
            if not raw:
                pool.mark_error(idx)
                continue
            data = extract_json_array(raw)
            if not data:
                pool.mark_error(idx)
                continue
            valid = [q for q in data if (
                isinstance(q, dict) and q.get('question')
                and isinstance(q.get('options'), list) and len(q['options']) == 4
                and isinstance(q.get('correct_answer'), int)
                and 0 <= q['correct_answer'] <= 3
            )]
            if valid:
                pool.mark_success(idx)
                print(f'      ✅ {len(valid)}/{len(data)} via {pool.name.lower()}', flush=True)
                return valid
        except Exception as e:
            err = str(e)
            if '429' in err or 'rate' in err.lower() or 'timed out' in err.lower():
                pool.mark_rate_limit(idx, cooldown=90)
            elif '401' in err or '403' in err:
                pool.mark_dead(idx, reason='invalid key')
            else:
                pool.mark_error(idx)
            continue
    return []


def verify_via_groq(q, level):
    """Fallback verifier when Gemini is exhausted"""
    if not GEN_PROVIDERS: return False, 0, 'no providers'
    for name, client, model in GEN_PROVIDERS[:3]:
        try:
            prompt = f"""Rate this MCQ for difficulty {level}/10.
Q: {q.get('question','')}
Options: {q.get('options',[])}
Correct index: {q.get('correct_answer',0)}
Return ONLY JSON: {{"passed": true, "score": 9, "reason": "..."}}"""
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=200,
            )
            txt = r.choices[0].message.content.strip()
            import re as _re
            m = _re.search(r'\{.*\}', txt, _re.DOTALL)
            if m:
                d = json_repair.loads(m.group())
                return d.get('passed', False), d.get('score', 0), d.get('reason', '')
        except Exception:
            continue
    return False, 0, 'no verifier'

def verify(q, level):
    if not GEMINI_POOL:
        return verify_via_groq(q, level)

    idx, key = GEMINI_POOL.get_key(wait=True)
    if key is None:
        return verify_via_groq(q, level)

    model = GEMINI_KEY_TO_MODEL[key]
    try:
        client = genai.Client(api_key=key)
        prompt = f"""Rate this MCQ for difficulty {level}/10.

Q: {q.get('question','')}
Options: {q.get('options',[])}
Correct index: {q.get('correct_answer',0)}

Return ONLY JSON: {{"passed": true, "score": 9, "reason": "..."}}
Score 9+ if factually correct, clear, plausible distractors."""
        r = client.models.generate_content(model=model, contents=prompt)
        txt = (r.text or '').strip()
        txt = re.sub(r'^```json\s*|\s*```$', '', txt, flags=re.MULTILINE).strip()
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if not m:
            GEMINI_POOL.mark_error(idx)
            return verify_via_groq(q, level)
        d = json_repair.loads(m.group())
        GEMINI_POOL.mark_success(idx)
        return d.get('passed', False), d.get('score', 0), d.get('reason', '')
    except Exception as e:
        err = str(e)
        if '429' in err or 'quota' in err.lower() or 'rate' in err.lower():
            # Put key in cooldown for 60s
            GEMINI_POOL.mark_rate_limit(idx, cooldown=120)
            # Try Groq immediately
            return verify_via_groq(q, level)
        elif '401' in err or '403' in err or 'API_KEY_INVALID' in err:
            GEMINI_POOL.mark_dead(idx, reason='invalid key')
            return verify_via_groq(q, level)
        else:
            GEMINI_POOL.mark_error(idx)
            return verify_via_groq(q, level)


def save(q, topic_id, subject_id, level, score, exam_tags):
    rec = {
        "id": f"q_{uuid.uuid4().hex[:16]}",
        "topic_id": topic_id, "subject_id": subject_id, "level": level,
        "difficulty": "Easy" if level <= 3 else "Medium" if level <= 6 else "Hard" if level <= 8 else "Expert",
        "pattern_type": "standalone_mcq4",
        "question_en": q["question"], "options_en": q["options"],
        "correct_answer": q["correct_answer"],
        "explanation": {
            "why_correct": q.get("why_correct",""),
            "why_wrong_option_b": q.get("why_wrong_option_b",""),
            "why_wrong_option_c": q.get("why_wrong_option_c",""),
            "why_wrong_option_d": q.get("why_wrong_option_d",""),
            "story_explanation": q.get("story_explanation",""),
            "shortcut_tips": q.get("shortcut_tips",""),
            "cross_exam_intelligence": q.get("cross_exam_intelligence",""),
        },
        "translations": {}, "exam_tags": exam_tags,
        "has_visual": False, "visual_type": None, "visual_data": None,
        "access_tier": "free" if level <= 6 else "pro",
        "copyright_original": True, "verified": True, "quality_score": score,
        "report_count": 0, "generated_by": "tryit_v2",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        s.table('questions').insert(rec).execute()
        return True
    except Exception as e:
        print(f'      ❌ Save: {str(e)[:100]}')
        return False

def process_topic_level(topic_id, topic_name, subject_id, level, target, exam_tags):
    existing = get_existing_count(topic_id, level)
    if existing >= target:
        return 0
    needed = target - existing
    print(f'   ⏳ {topic_id} L{level}: {existing}/{target} → need {needed}')
    saved = 0
    empty_rounds = 0
    while saved < needed and empty_rounds < 5:
        batch_n = min(BATCH_SIZE, needed - saved)
        qs = generate_batch(topic_id, topic_name, subject_id, level, batch_n, exam_tags)
        if not qs:
            empty_rounds += 1
            time.sleep(3)
            continue
        empty_rounds = 0
        for q in qs:
            ok, score, reason = verify(q, level)
            if not ok or score < QUALITY_THRESHOLD:
                continue
            if save(q, topic_id, subject_id, level, score, exam_tags):
                saved += 1
        time.sleep(0.5)
    print(f'   🎉 {topic_id} L{level}: +{saved} saved')
    return saved

def process_topic(topic):
    tid = topic['topic_id']
    tname = topic.get('topic_name', tid)
    sid = topic.get('subject_id') or 'general'
    dr = topic.get('difficulty_range') or '2-7'
    try:
        lo, hi = map(int, dr.split('-'))
    except Exception:
        lo, hi = 2, 7
    try:
        exam_tags = sorted(set(r['exam_id'] for r in (
            s.table('exam_syllabus_map').select('exam_id').eq('topic_id', tid).execute().data or []
        )))
    except Exception:
        exam_tags = []
    print(f'\n📘 {tid} [L{lo}-L{hi}] exams={exam_tags[:4]}')
    total = 0
    for lvl in range(lo, hi+1):
        target = TARGET_L1_L5 if lvl <= 5 else TARGET_L6_L10
        total += process_topic_level(tid, tname, sid, lvl, target, exam_tags)
    return total

def main():
    topics = s.table('topics').select('topic_id, topic_name, subject_id, difficulty_range, coverage_score').order('coverage_score', desc=True).execute().data
    if MAX_TOPICS:
        topics = topics[:MAX_TOPICS]
    print(f'\n📚 {len(topics)} topics queued\n')
    grand_total = 0
    with ThreadPoolExecutor(max_workers=CONCURRENT_WORKERS) as ex:
        futures = {ex.submit(process_topic, t): t['topic_id'] for t in topics}
        for fut in as_completed(futures):
            try:
                grand_total += fut.result()
            except Exception as e:
                print(f"   !! {futures[fut]}: {e}")
    print(f'\n✅ DONE. Total new: {grand_total}')

if __name__ == "__main__":
    main()
