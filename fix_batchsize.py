content = open('generate_master.py', encoding='utf-8').read()

# Fix the NameError - BATCH_SIZE was replaced by get_batch_size() function
old = 'print(f"  Groq GEN: {len(GROQ_KEYS)} keys | 1000 RPD org | batch={BATCH_SIZE}", flush=True)'
new = 'print(f"  Groq GEN: {len(GROQ_KEYS)} keys | 1000 RPD org | batch=5-7 (dynamic)", flush=True)'

if old in content:
    content = content.replace(old, new)
    print("FIXED: BATCH_SIZE NameError")
else:
    print("SEARCHING for BATCH_SIZE references...")
    for i, line in enumerate(content.split('\n')):
        if 'BATCH_SIZE' in line:
            print(f"  Line {i}: {line.strip()}")

open('generate_master.py', 'w', encoding='utf-8').write(content)
