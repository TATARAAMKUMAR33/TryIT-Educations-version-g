content = open("generate_master.py", encoding="utf-8").read()

old = '''        key = f"{r.get("topic_id")}_{r.get("level")}"
            _count_cache[key] = _count_cache.get(key,0) + 1'''

new = '''        tid = r.get("topic_id")
            lvl = r.get("level")
            key = f"{tid}_{lvl}"
            _count_cache[key] = _count_cache.get(key,0) + 1'''

if old in content:
    content = content.replace(old, new)
    print("FIXED: f-string quote conflict")
else:
    print("MISS - searching...")
    for i,l in enumerate(content.split("\n")):
        if "topic_id" in l and "count_cache" in l:
            print(f"  Line {i}: {repr(l)}")

open("generate_master.py", "w", encoding="utf-8").write(content)
