content = open('generate_master.py', encoding='utf-8').read()
for i, line in enumerate(content.split('\n')):
    if 'import requests' in line or 'import os' in line:
        print(f'{i}: {repr(line)}')
