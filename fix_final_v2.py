content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix 1: Count cache - fetch ALL questions not just 1000
old1 = '''        rows = s.table("questions").select("topic_id,level").execute().data or []'''
new1 = '''        rows = []
        offset = 0
        while True:
            batch = s.table("questions").select("topic_id,level").range(offset, offset+999).execute().data or []
            rows.extend(batch)
            if len(batch) < 1000: break
            offset += 1000
        print(f"Cache: fetched {len(rows)} total questions", flush=True)'''
if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print("Fix 1 OK: Cache fetches ALL questions")
else:
    print("Fix 1 MISS")

# Fix 2: SambaNova as PRIMARY generator (before Groq)
old2 = '''    # PRIMARY: Groq (1,000 RPD org-wide) - only if keys available
    if GROQ_POOL and not GROQ_POOL.all_cooling():
        groq_rate_wait()
        for model in ["openai/gpt-oss-120b","openai/gpt-oss-20b"]:
            raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=5000, timeout=60, label="Groq")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q Groq {model} L{level}", flush=True)
                    return valid'''
new2 = '''    # PRIMARY: SambaNova (high RPD, no org-wide limit)
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
                    return valid'''
if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: SambaNova is now PRIMARY generator")
else:
    print("Fix 2 MISS - checking...")
    for i,l in enumerate(content.split("\n")):
        if "PRIMARY" in l:
            print(f"  Line {i}: {l.strip()}")

# Fix 3: Remove dead Gemini key 2 from probe (saves 30s startup)
old3 = '''GEMINI_MODELS = [
    "gemini-3.5-flash","gemini-2.5-flash",
    "gemini-2.0-flash","gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite","gemini-1.5-flash","gemini-1.5-flash-8b"
]'''
new3 = '''GEMINI_MODELS = [
    "gemini-2.5-flash","gemini-3.5-flash",
    "gemini-2.0-flash","gemini-1.5-flash"
]'''
if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: Gemini model list cleaned")
else:
    print("Fix 3 MISS")

# Fix 4: Reduce empty wait - 5s max not 30s
old4 = '''empty_wait = 5 if empty < 2 else 30
            print(f"   Empty {empty}/3 - wait {empty_wait}s", flush=True)
            time.sleep(empty_wait)'''
new4 = '''empty_wait = 5
            print(f"   Empty {empty}/3 - wait {empty_wait}s", flush=True)
            time.sleep(empty_wait)'''
if old4 in content:
    content = content.replace(old4, new4)
    fixes += 1
    print("Fix 4 OK: Empty wait always 5s")
else:
    print("Fix 4 MISS")

open("generate_master.py","w",encoding="utf-8").write(content)
print(f"\nTotal fixes: {fixes}/4")

# Verify
for i,l in enumerate(content.split("\n")):
    if "PRIMARY" in l or "SECONDARY" in l:
        print(f"  Line {i}: {l.strip()}")
