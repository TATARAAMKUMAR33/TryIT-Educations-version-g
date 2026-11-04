import re
content = open('generate_master.py', encoding='utf-8').read()

# Remove all emojis and special unicode characters, replace with ASCII
replacements = {
    '\U0001f511': '',  # key emoji
    '\U0001f50e': '',  # magnifier
    '\U0001f680': '',  # rocket
    '\u2501': '-',     # box drawing
    '\u2550': '=',     # box drawing
    '\u2794': '->',    # arrow
    '\u2705': 'OK',    # checkmark
    '\u274c': 'FAIL',  # cross
    '\u23f3': '...',   # hourglass
    '\u26a0': '!!',    # warning
    '\U0001f4cb': '',  # clipboard
    '\U0001f4d8': '',  # book
    '\U0001f389': '',  # party
    '\U0001f4be': '',  # floppy
    '\U0001f52c': '',  # microscope
    '\U0001f9ea': '',  # test tube
    '\u231b': '...',   # hourglass2
    '\U0001f6a8': '!!', # siren
    '\u2615': '',      # coffee
    '\u2714': 'OK',    # checkmark2
    '\u23f0': '',      # alarm
    '\u2764': '',      # heart
    '\U0001f4aa': '',  # muscle
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Remove any remaining non-ASCII non-printable chars from print strings
import re
# Replace remaining emoji/unicode in f-strings with nothing
content = re.sub(r'[^\x00-\x7F]', '', content)

open('generate_master.py', 'w', encoding='utf-8').write(content)
print('All emojis removed')
