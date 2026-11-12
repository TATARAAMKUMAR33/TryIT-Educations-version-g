content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix 1: UUID collision - add timestamp to make truly unique
old1 = '"id":               f"q_{uuid.uuid4().hex[:16]}",'
new1 = '"id":               f"q_{uuid.uuid4().hex[:12]}{int(time.time()*1000)%10000:04d}",'
if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print("Fix 1 OK: UUID collision fix")
else:
    print("Fix 1 MISS - searching id field...")
    for i,l in enumerate(content.split("\n")):
        if '"id"' in l and "uuid" in l and "question" not in l.lower():
            print(f"  Line {i}: {l.strip()}")

# Fix 2: Dead Gemini keys - add gemini-2.0-flash to model list
old2 = 'GEMINI_MODELS = [\n    "gemini-3.5-flash","gemini-2.5-flash",\n    "gemini-2.5-flash-lite","gemini-1.5-flash"\n]'
new2 = 'GEMINI_MODELS = [\n    "gemini-3.5-flash","gemini-2.5-flash",\n    "gemini-2.0-flash","gemini-2.0-flash-lite",\n    "gemini-2.5-flash-lite","gemini-1.5-flash","gemini-1.5-flash-8b"\n]'
if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: Added gemini-2.0-flash models")
else:
    print("Fix 2 MISS - checking GEMINI_MODELS...")
    for i,l in enumerate(content.split("\n")):
        if "GEMINI_MODELS" in l or "gemini-3.5" in l:
            print(f"  Line {i}: {l.strip()}")

# Fix 3: QA pool split - use key index >= 2 for QA (not >=3)
# since we only have 2 working keys
old3 = "GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 3]\nGEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 3]"
new3 = "GEMINI_GEN_KEYS = [k for i,k in enumerate(GEMINI_WORKING) if i < 2]\nGEMINI_QA_KEYS  = [k for i,k in enumerate(GEMINI_WORKING) if i >= 2]"
if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: QA split adjusted for 2 working keys")
else:
    print("Fix 3 MISS - checking key split...")
    for i,l in enumerate(content.split("\n")):
        if "GEMINI_GEN_KEYS" in l or "GEMINI_QA_KEYS" in l:
            print(f"  Line {i}: {l.strip()}")

open("generate_master.py", "w", encoding="utf-8").write(content)
print(f"\nFixes applied: {fixes}/3")
