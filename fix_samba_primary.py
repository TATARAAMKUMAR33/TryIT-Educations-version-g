content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix: When Groq rate limited, don't wait - go straight to SambaNova
old1 = '''    # PRIMARY: Groq (1,000 RPD org-wide)
    groq_rate_wait()
    for model in ["openai/gpt-oss-120b","openai/gpt-oss-20b"]:
        raw = call_openai(GROQ_POOL, GROQ_CLIENTS, model, msgs, max_tokens=5000, timeout=60, label="Groq")
        if raw:
            data  = extract_list(raw)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q Groq {model} L{level}", flush=True)
                return valid'''

new1 = '''    # PRIMARY: Groq (1,000 RPD org-wide) - only if keys available
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

if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print("Fix 1 OK: Skip Groq when all rate limited")
else:
    print("Fix 1 MISS")

# Fix 2: Add all_cooling method check - SambaNova first when Groq exhausted
old2 = '''    # SECONDARY: Gemini generation (3 keys x 500 RPD)
    if GEMINI_GEN_POOL:'''

new2 = '''    # SECONDARY-A: SambaNova when Groq exhausted (unlimited RPD)
    if SAMBA_POOL and SAMBA_CLIENTS:
        for model in ["Meta-Llama-3.3-70B-Instruct","Meta-Llama-3.1-405B-Instruct"]:
            raw = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=60, label="SambaNova")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q SambaNova {model} L{level}", flush=True)
                    return valid

    # SECONDARY-B: Gemini generation (3 keys x 500 RPD)
    if GEMINI_GEN_POOL:'''

if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: SambaNova promoted to secondary")
else:
    print("Fix 2 MISS")

# Fix 3: Add all_cooling method to key pool usage
old3 = '''    # TERTIARY: SambaNova emergency fallback
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

    print(f"      All generators failed L{level}", flush=True)
    return []'''

new3 = '''    print(f"      All generators failed L{level}", flush=True)
    return []'''

if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: Removed duplicate SambaNova block")
else:
    print("Fix 3 MISS - ok if not found")
    fixes += 1

open("generate_master.py", "w", encoding="utf-8").write(content)
print(f"\nFixes: {fixes}/3")
print(f"Lines: {content.count(chr(10))}")

# Verify SambaNova is now secondary
for i,l in enumerate(content.split("\n")):
    if "SECONDARY" in l:
        print(f"  Line {i}: {l.strip()}")
