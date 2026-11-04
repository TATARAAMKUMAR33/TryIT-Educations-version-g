content = open('generate_master.py', encoding='utf-8').read()

# Fix the broken indentation
old = 'groq_rate_wait()\n        for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'
new = '    groq_rate_wait()\n    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'

if old in content:
    content = content.replace(old, new)
    print('Fixed OK')
else:
    # Find actual indentation
    for i, line in enumerate(content.split('\n')):
        if 'groq_rate_wait' in line or ('for model in' in line and 'gpt-oss' in line):
            print(f'Line {i}: {repr(line)}')

open('generate_master.py', 'w', encoding='utf-8').write(content)
