content = open('generate_master.py', encoding='utf-8').read()

# Find and fix ALL occurrences of undefined constants
replacements = [
    ('QUALITY_THRESHOLD', '7'),
    ('BATCH_SIZE', '7'),
]

fixes = 0
for old_name, replacement in replacements:
    import re
    # Find all lines with this name
    lines_found = [(i+1, l) for i,l in enumerate(content.split('\n')) if old_name in l]
    for lnum, ltext in lines_found:
        print(f"Found {old_name} at line {lnum}: {ltext.strip()}")
        fixed = ltext.replace(old_name, replacement)
        content = content.replace(ltext, fixed)
        fixes += 1

print(f"\nTotal fixes: {fixes}")
open('generate_master.py', 'w', encoding='utf-8').write(content)

# Verify
for name in ['QUALITY_THRESHOLD', 'BATCH_SIZE']:
    count = content.count(name)
    print(f"{name} remaining: {count}")
