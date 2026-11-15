with open("generate_master.py", "rb") as f:
    raw = f.read()

# Replace the entire generator section by line numbers 443-492
lines = raw.decode("utf-8").split("\n")
print(f"Total lines: {len(lines)}")
print(f"Line 443: {repr(lines[443][:60])}")
print(f"Line 492: {repr(lines[492][:60])}")

new_block = """    # PRIMARY: OpenRouter (free models, no daily limit)
    if OR_POOL and OR_CLIENTS:
        for model in OR_FREE_MODELS:
            raw = call_openai(OR_POOL, OR_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=90, label="OpenRouter")
            if raw:
                data  = extract_list(raw)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q OR {model.split(chr(47))[-1]} L{level}", flush=True)
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
            raw_s = call_openai(SAMBA_POOL, SAMBA_CLIENTS, model, msgs,
                            max_tokens=4000, timeout=60, label="SambaNova")
            if raw_s:
                data  = extract_list(raw_s)
                valid = validate_qs(data)
                if valid:
                    print(f"      {len(valid)}q SambaNova {model} L{level}", flush=True)
                    return valid

    # QUATERNARY: Gemini
    if GEMINI_GEN_POOL:
        raw_g = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL,
                               f"{sys_msg}\\n\\n{prompt}", "GeminiGen")
        if raw_g:
            data  = extract_list(raw_g)
            valid = validate_qs(data)
            if valid:
                print(f"      {len(valid)}q GeminiGen L{level}", flush=True)
                return valid

    print(f"      All generators failed L{level}", flush=True)
    return []"""

# Replace lines 443 to 492 inclusive
new_lines = lines[:443] + new_block.split("\n") + lines[493:]
result = "\n".join(new_lines)
with open("generate_master.py", "w", encoding="utf-8", newline="\n") as f:
    f.write(result)
print("Done")
print(f"New line count: {result.count(chr(10))}")
for i,l in enumerate(result.split("\n")):
    if any(x in l for x in ["# PRIMARY","# SECONDARY","# TERTIARY","# QUATERNARY"]):
        print(f"  L{i}: {l.strip()}")
