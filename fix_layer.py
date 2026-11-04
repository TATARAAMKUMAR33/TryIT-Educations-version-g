content = open('generate_master.py', encoding='utf-8').read()

old = '    missing = [f for f in required if not q.get(f) or len(str(q.get(f,""))) < 20]\n    if missing:\n        print(f"       Missing layers: {missing}", flush=True)\n        return False, 0, f"missing: {missing}"'

new = '    # Only reject if core layers missing - optional layers just warn\n    core = ["why_correct","story_explanation"]\n    missing = [f for f in required if not q.get(f) or len(str(q.get(f,""))) < 20]\n    missing_core = [f for f in core if not q.get(f) or len(str(q.get(f,""))) < 20]\n    if missing_core:\n        print(f"       Missing core layers: {missing_core}", flush=True)\n        return False, 0, f"missing core: {missing_core}"\n    if missing:\n        print(f"       Weak layers (saving anyway): {missing}", flush=True)'

if old in content:
    content = content.replace(old, new)
    print('Fixed OK')
else:
    print('NO MATCH')

open('generate_master.py', 'w', encoding='utf-8').write(content)
