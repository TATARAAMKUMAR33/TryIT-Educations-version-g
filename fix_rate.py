content = open('generate_master.py', encoding='utf-8').read()

old = 'GROQ_CLIENTS = {k: OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k) for k in GROQ_KEYS}'
new = 'GROQ_CLIENTS = {k: OpenAI(base_url="https://api.groq.com/openai/v1", api_key=k) for k in GROQ_KEYS}\nimport threading as _th\n_groq_lock = _th.Lock()\n_groq_last = [0.0]\ndef groq_rate_wait():\n    with _groq_lock:\n        gap = 2.5 - (time.time() - _groq_last[0])\n        if gap > 0:\n            time.sleep(gap)\n        _groq_last[0] = time.time()'

if old in content:
    content = content.replace(old, new)
    print('Rate limiter added OK')
else:
    print('NO MATCH')

old2 = 'for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'
new2 = 'groq_rate_wait()\n        for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'

if old2 in content:
    content = content.replace(old2, new2)
    print('Call added OK')
else:
    print('NO MATCH call')

open('generate_master.py', 'w', encoding='utf-8').write(content)
