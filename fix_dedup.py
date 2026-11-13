content = open("generate_master.py", encoding="utf-8").read()

# Remove duplicate SambaNova block (the old SECONDARY-A one)
old = '''    # SECONDARY-A: SambaNova when Groq exhausted (unlimited RPD)
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

    # SECONDARY-B: Gemini generation (3 keys x 500 RPD)'''
new = '''    # TERTIARY: Gemini generation (3 keys x 500 RPD)'''

if old in content:
    content = content.replace(old, new)
    print("Duplicate removed OK")
else:
    print("MISS - counting SambaNova blocks:")
    print(content.count("SECONDARY-A"), "SECONDARY-A blocks")
    print(content.count("SECONDARY-B"), "SECONDARY-B blocks")
    # Show all generator section lines
    for i,l in enumerate(content.split("\n")):
        if any(x in l for x in ["PRIMARY","SECONDARY","TERTIARY"]):
            print(f"  L{i}: {l.strip()}")

open("generate_master.py","w",encoding="utf-8").write(content)
print(f"Lines: {content.count(chr(10))}")
