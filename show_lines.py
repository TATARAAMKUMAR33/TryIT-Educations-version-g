content = open('generate_master.py', encoding='utf-8').read()
lines = content.split('\n')
for i, line in enumerate(lines[350:365], start=350):
    print(f'{i}: {repr(line)}')
