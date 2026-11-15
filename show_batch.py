content = open("generate_master.py", encoding="utf-8").read()
lines = content.split("\n")

# Find the generate_batch function boundaries
start = None
for i,l in enumerate(lines):
    if "def generate_batch(" in l:
        start = i
        break

print(f"generate_batch starts at line {start}")
# Show lines 440-500
for i in range(440, min(500, len(lines))):
    print(f"L{i}: {repr(lines[i][:80])}")
