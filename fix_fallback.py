content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix 1: Add SambaNova as emergency fallback generator
old1 = '# ── NVIDIA SETUP ──────────────────────────────────────────────────────────────'
new1 = '''# ── SAMBANOVA EMERGENCY FALLBACK ─────────────────────────────────────────────
SAMBA_KEYS = []
for i in range(1,6):
    k = os.getenv(f"SAMBANOVA_API_KEY_{i}") or os.getenv("SAMBANOVA_API_KEY")
    if k and k.strip() and k not in SAMBA_KEYS:
        SAMBA_KEYS.append(k.strip())

SAMBA_CLIENTS = {}
SAMBA_POOL = None
if SAMBA_KEYS:
    SAMBA_CLIENTS = {k: OpenAI(
        base_url="https://api.sambanova.ai/v1", api_key=k) for k in SAMBA_KEYS}
    SAMBA_POOL = get_pool("SambaNova", SAMBA_KEYS, cooldown_seconds=65)
    print(f"SambaNova fallback: {len(SAMBA_KEYS)} keys", flush=True)

# ── NVIDIA SETUP ──────────────────────────────────────────────────────────────'''

if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print("Fix 1 OK: SambaNova fallback added")
else:
    print("Fix 1 MISS")

# Fix 2: Add SambaNova to generate_batch fallback chain
old2 = '''    print(f"      All generators failed L{level}", flush=True)
    return []'''
new2 = '''    # TERTIARY: SambaNova emergency fallback
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

if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: SambaNova added to fallback chain")
else:
    print("Fix 2 MISS: fallback return not found")

# Fix 3: When ALL rate limited sleep 30s not 5s to let limits reset
old3 = '''   Empty 1/3 - wait 5s", flush=True)
            time.sleep(5)'''
# This is in the log not code - find actual code
old3 = 'print(f"   Empty {empty}/3 - wait 5s", flush=True)\n            time.sleep(5)'
new3 = '''empty_wait = 5 if empty < 2 else 30
            print(f"   Empty {empty}/3 - wait {empty_wait}s", flush=True)
            time.sleep(empty_wait)'''
if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: Backoff wait on empty")
else:
    print("Fix 3 MISS - checking sleep...")
    for i,l in enumerate(content.split("\n")):
        if "Empty" in l and "wait" in l:
            print(f"  Line {i}: {l.strip()}")

open("generate_master.py", "w", encoding="utf-8").write(content)
print(f"\nFixes: {fixes}/3")
