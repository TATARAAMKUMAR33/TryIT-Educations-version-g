content = open('generate_master.py', encoding='utf-8').read()

# Find exact string
idx = content.find('missing = [f for f in required')
if idx == -1:
    print('Not found')
else:
    print('Found at char:', idx)
    print(repr(content[idx-100:idx+200]))
