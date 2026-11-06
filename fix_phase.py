content = open('generate_master.py', encoding='utf-8').read()

old = '.eq("launch_phase", "phase_1_now")'
new = '.in_("launch_phase", ["phase_1_now", "phase_2_2027"])'

if old in content:
    content = content.replace(old, new)
    print('Phase filter updated OK')
else:
    print('NO MATCH - checking...')
    for i, line in enumerate(content.split('\n')):
        if 'launch_phase' in line:
            print(f'Line {i}: {line.strip()}')

open('generate_master.py', 'w', encoding='utf-8').write(content)
