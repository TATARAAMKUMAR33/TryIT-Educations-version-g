content = open('generate_master.py', encoding='utf-8').read()

# Fix 1: Increase max_tokens for Groq generation
content = content.replace(
    'max_tokens=4096, timeout=60, label="Groq")',
    'max_tokens=6000, timeout=90, label="Groq")'
)
print('Groq tokens: OK' if '6000' in content else 'Groq tokens: FAIL')

# Fix 2: Suppress the FutureWarning (cosmetic only, not breaking)
old_import = 'import os, json, time, uuid, re, requests'
new_import = 'import os, json, time, uuid, re, requests, warnings\nwarnings.filterwarnings("ignore")'
content = content.replace(old_import, new_import)
print('Warning suppress: OK' if 'filterwarnings' in content else 'Warning suppress: FAIL')

open('generate_master.py', 'w', encoding='utf-8').write(content)
