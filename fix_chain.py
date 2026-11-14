content = open("generate_master.py", encoding="utf-8").read()

# Replace lines 443-493 — the entire messy generator section
# Find by unique text that exists once
old = '''    # PRIMARY: SambaNova (high RPD, no org-wide limit)
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

new = '''    # PRIMARY: OpenRouter (free models, no daily limit)
    if OR_POOL and OR_CLIENTS:
        for model in OR_FREE_MODELS:
            raw = call_openai(OR_POOL, OR_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=90, label="OpenRouter")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q OR {model.split('/')[-1]} L{level}", flush=True)
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

if old in content:
    content = content.replace(old, new)
    print("FIXED: Generator chain cleaned")
else:
    print(f"MISS: checking counts...")
    print(f"  SECONDARY-A: {content.count('SECONDARY-A')}")
    print(f"  SambaNova blocks: {content.count('PRIMARY: SambaNova')}")

open("generate_master.py","w",encoding="utf-8").write(content)
print(f"Lines: {content.count(chr(10))}")

print("\nFinal chain:")
for i,l in enumerate(content.split("\n")):
    if any(x in l for x in ["# PRIMARY","# SECONDARY","# TERTIARY","# QUATERNARY"]):
        print(f"  L{i}: {l.strip()}")
