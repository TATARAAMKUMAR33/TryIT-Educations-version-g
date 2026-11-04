content = open('generate_master.py', encoding='utf-8').read()

old = '    #  PRIMARY: Groq (1,000 RPD org-wide, fastest) \n        groq_rate_wait()\n    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'
new = '    #  PRIMARY: Groq (1,000 RPD org-wide, fastest)\n    groq_rate_wait()\n    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'

if old in content:
    content = content.replace(old, new)
    print('Fixed OK')
else:
    print('NO MATCH - trying alternate')
    old2 = '        groq_rate_wait()\n    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'
    new2 = '    groq_rate_wait()\n    for model in ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]:'
    if old2 in content:
        content = content.replace(old2, new2)
        print('Fixed via alternate OK')
    else:
        print('BOTH FAILED')

open('generate_master.py', 'w', encoding='utf-8').write(content)
