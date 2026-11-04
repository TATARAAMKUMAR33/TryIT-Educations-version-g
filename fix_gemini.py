import requests as req
content = open('generate_master.py', encoding='utf-8').read()

old = 'genai.Client(api_key=k).models.generate_content(model=model, contents="hi")'
new = '''url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={k}"
            r = req.post(url, json={"contents":[{"parts":[{"text":"hi"}]}]}, timeout=15)
            if r.status_code != 200:
                print(f"  FAIL Gemini key {model}: {r.status_code}", flush=True)
                continue
            _ = r'''

if old in content:
    content = content.replace(old, new)
    open('generate_master.py', 'w', encoding='utf-8').write(content)
    print('FIXED')
else:
    print('NO MATCH')
    for i,line in enumerate(content.split('\n')):
        if 'genai.Client' in line:
            print(f'Line {i}: {line.strip()}')
