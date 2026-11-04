content = open('generate_master.py', encoding='utf-8').read()

# Fix 1: Replace local req import with top-level requests
old = 'import requests as req\nfor i, k in enumerate(GEMINI_KEYS):'
new = 'for i, k in enumerate(GEMINI_KEYS):'
if old in content:
    content = content.replace(old, new)
    print('Removed local req import OK')
else:
    print('Local req import not found - checking...')
    if 'import requests as req' in content:
        content = content.replace('import requests as req\n', '')
        print('Removed standalone req import OK')
    else:
        print('No req import found at all')

# Add requests import at top with other imports
if 'import requests' not in content:
    content = content.replace(
        'import os, json, time, uuid, re',
        'import os, json, time, uuid, re, requests'
    )
    print('Added requests to top imports OK')
else:
    print('requests already imported')

# Fix the url line to use requests directly
old2 = 'r = req.post(url,'
new2 = 'r = requests.post(url,'
if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed req.post to requests.post OK')

# Fix 2: Reduce workers to 1 to stop simultaneous Groq hammering
old3 = 'CONCURRENT_WORKERS = 3'
new3 = 'CONCURRENT_WORKERS = 1'
if old3 in content:
    content = content.replace(old3, new3)
    print('Workers reduced to 1 OK')

open('generate_master.py', 'w', encoding='utf-8').write(content)
