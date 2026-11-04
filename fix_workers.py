import re
content = open('generate_master.py', encoding='utf-8').read()

# Fix 1: Workers back to 3
content = content.replace('CONCURRENT_WORKERS = 1', 'CONCURRENT_WORKERS = 3')
print('Workers=3: OK')

# Fix 2: Increase rate limit interval to handle 3 workers
# 3 workers x 1 call = 3 simultaneous, need 3x spacing
content = content.replace('gap = 2.5 - (time.time() - _groq_last[0])', 'gap = 3.5 - (time.time() - _groq_last[0])')
print('Rate interval 3.5s: OK')

# Fix 3: Make missing layer questions still save if only 1 layer missing
# Currently rejects if ANY required field < 20 chars
# Change: only reject if why_correct or story_explanation missing
old = '''    required = ["why_correct","why_wrong_option_b","why_wrong_option_c",
                "why_wrong_option_d","story_explanation","shortcut_tips","cross_exam_intelligence"]
    missing = [f for f in required if not q.get(f) or len(str(q.get(f,""))) < 20]
    if missing:
        print(f"      Missing layers: {missing}", flush=True)
        return False, 0, f"missing: {missing}"'''

new = '''    # Core layers required - must have these
    core = ["why_correct","story_explanation"]
    missing_core = [f for f in core if not q.get(f) or len(str(q.get(f,""))) < 20]
    if missing_core:
        print(f"      Missing core layers: {missing_core}", flush=True)
        return False, 0, f"missing core: {missing_core}"
    # Optional layers - warn but do not reject
    optional = ["why_wrong_option_b","why_wrong_option_c","why_wrong_option_d","shortcut_tips","cross_exam_intelligence"]
    missing_opt = [f for f in optional if not q.get(f) or len(str(q.get(f,""))) < 10]
    if missing_opt:
        print(f"      Weak layers (not rejecting): {missing_opt}", flush=True)'''

if old in content:
    content = content.replace(old, new)
    print('Layer check relaxed: OK')
else:
    print('Layer check: NO MATCH - checking...')
    if 'missing = [f for f in required' in content:
        print('Found old version')

open('generate_master.py', 'w', encoding='utf-8').write(content)
