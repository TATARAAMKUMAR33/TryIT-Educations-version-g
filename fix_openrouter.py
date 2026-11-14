"""
fix_openrouter.py
Adds OpenRouter as PRIMARY generator with 10+ free models
Replaces broken SambaNova-primary setup
"""
content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix 1: Add OpenRouter setup after NVIDIA setup
old1 = '# ── EMIT TIER PRIORITY MAP ───────────────────────────────────────────────────'
# Try alternate marker
if old1 not in content:
    old1 = '# ── EXAM DIFFICULTY MATRIX ──────────────────────────────────────────────────'

new1_prefix = '''# ── OPENROUTER SETUP (Primary - 10+ free models, no daily limit) ────────────
OR_KEYS = []
for i in range(1,6):
    k = os.getenv(f"OPENROUTER_API_KEY_{i}") or os.getenv("OPENROUTER_API_KEY")
    if k and k.strip() and k not in OR_KEYS:
        OR_KEYS.append(k.strip())

OR_CLIENTS = {}
OR_POOL = None
if OR_KEYS:
    OR_CLIENTS = {k: OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=k) for k in OR_KEYS}
    OR_POOL = get_pool("OpenRouter", OR_KEYS, cooldown_seconds=30)
    print(f"OpenRouter: {len(OR_KEYS)} keys loaded", flush=True)

# Free models on OpenRouter (no daily limit, 20 RPM each)
OR_FREE_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "deepseek/deepseek-r1-distill-llama-70b:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.1-8b-instruct:free",
    "microsoft/phi-3-medium-128k-instruct:free",
]

'''

if old1 in content:
    content = content.replace(old1, new1_prefix + old1)
    fixes += 1
    print("Fix 1 OK: OpenRouter setup added")
else:
    print("Fix 1 MISS - finding insert point...")
    for i,l in enumerate(content.split("\n")):
        if "EXAM DIFFICULTY" in l or "TIER PRIORITY" in l or "SUBJECT_TIER" in l:
            print(f"  L{i}: {l.strip()}")

# Fix 2: Replace entire generate_batch function with clean version
old2 = '''def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags, exam_patterns):
    context = get_context(topic_id, subject_id) if callable(get_context) else ""
    prompt  = build_prompt(topic_name, subject_id, level, count, exam_tags, context, exam_patterns)

    sys_msg = "JSON-only MCQ generator. Output ONLY a valid JSON array. Never add text outside JSON."
    msgs = [
        {"role":"system","content":sys_msg},
        {"role":"user","content":prompt}
    ]

    # PRIMARY: SambaNova (high RPD, no org-wide limit)
    if SAMBA_POOL and SAMBA_CLIENTS:
        for model in ["Meta-Llama-3.3-70B-Instruct","Qwen2.5-72B-Instruct",
                      "Meta-Llama-3.1-405B-Instruct"]:
            raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=60, label="SambaNova")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q SambaNova {model} L{level}", flush=True)
                    return valid

    # SECONDARY: Groq (1,000 RPD org-wide - backup only)
    if GROQ_POOL:
        groq_rate_wait()
        for model in ["openai/gpt-oss-120b","openai/gpt-oss-20b"]:
            raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=5000, timeout=60, label="Groq")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q Groq {model} L{level}", flush=True)
                    return valid

    # SECONDARY-A: SambaNova when Groq exhausted (unlimited RPD)
    if SAMBA_POOL and SAMBA_CLIENTS:
        for model in ["Meta-Llama-3.3-70B-Instruct","Meta-Llama-3.1-405B-Instruct",
                      "gemma-4-31B-it"]:
            raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=60, label="SambaNova")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q SambaNova {model} L{level}", flush=True)
                    return valid

    # SECONDARY-B: Gemini generation (3 keys x 500 RPD)
    if GEMINI_GEN_POOL:
        raw = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL,
                               f"{sys_msg}\\n\\n{prompt}", "GeminiGen")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q GeminiGen L{level}", flush=True)
                return valid

    print(f"      All generators failed L{level}", flush=True)
    return []'''

new2 = '''def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags, exam_patterns):
    context = get_context(topic_id, subject_id) if callable(get_context) else ""
    prompt  = build_prompt(topic_name, subject_id, level, count, exam_tags, context, exam_patterns)

    sys_msg = "JSON-only MCQ generator. Output ONLY a valid JSON array. Never add text outside JSON."
    msgs = [
        {"role":"system","content":sys_msg},
        {"role":"user","content":prompt}
    ]

    # PRIMARY: OpenRouter (free models, no daily limit, 20 RPM each)
    if OR_POOL and OR_CLIENTS:
        for model in OR_FREE_MODELS:
            raw = call_openai(OR_POOL, OR_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=90, label="OpenRouter")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q OpenRouter {model.split('/')[-1]} L{level}", flush=True)
                    return valid

    # SECONDARY: Groq (1,000 RPD org-wide)
    groq_rate_wait()
    for model in ["openai/gpt-oss-120b","openai/gpt-oss-20b"]:
        raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs,
                        max_tokens=5000, timeout=60, label="Groq")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q Groq {model} L{level}", flush=True)
                return valid

    # TERTIARY: SambaNova
    if SAMBA_POOL and SAMBA_CLIENTS:
        for model in ["Meta-Llama-3.3-70B-Instruct","Qwen2.5-72B-Instruct"]:
            raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=60, label="SambaNova")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q SambaNova {model} L{level}", flush=True)
                    return valid

    # QUATERNARY: Gemini
    if GEMINI_GEN_POOL:
        raw = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL,
                               f"{sys_msg}\\n\\n{prompt}", "GeminiGen")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q GeminiGen L{level}", flush=True)
                return valid

    print(f"      All generators failed L{level}", flush=True)
    return []'''

if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: generate_batch rewritten with clean priority chain")
else:
    print("Fix 2 MISS - generate_batch not found exactly")
    # Count how many times key phrases appear
    print(f"  'SECONDARY-A' count: {content.count('SECONDARY-A')}")
    print(f"  'SECONDARY-B' count: {content.count('SECONDARY-B')}")
    print(f"  'SambaNova' count: {content.count('SambaNova')}")

# Fix 3: Add OpenRouter to startup print
old3 = '    print(f"  Groq GEN: {len(GROQ_KEYS)} keys | 1000 RPD org | batch=5-7 (dynamic)", flush=True)'
new3 = '''    print(f"  OpenRouter: {len(OR_KEYS)} keys | free models | unlimited RPD", flush=True)
    print(f"  Groq GEN: {len(GROQ_KEYS)} keys | 1000 RPD org | batch=5-7 (dynamic)", flush=True)'''
if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: OpenRouter shown in startup")
else:
    print("Fix 3 MISS")

open("generate_master.py", "w", encoding="utf-8").write(content)
print(f"\nTotal fixes: {fixes}/3")
print(f"Lines: {content.count(chr(10))}")

# Verify chain order
print("\nGenerator chain:")
for i,l in enumerate(content.split("\n")):
    if any(x in l for x in ["# PRIMARY","# SECONDARY","# TERTIARY","# QUATERNARY"]):
        print(f"  L{i}: {l.strip()}")
