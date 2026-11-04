content = open('generate_master.py', encoding='utf-8').read()
for i, line in enumerate(content.split('\n')[:15]):
    print(f'{i}: {repr(line)}')
