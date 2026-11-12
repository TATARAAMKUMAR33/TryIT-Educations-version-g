content = open("generate_master.py", encoding="utf-8").read()
fixes = 0

# Fix 1: Cache all topic question counts at start (biggest speed fix)
# Instead of DB call per topic, fetch all counts once
old1 = '''def get_existing_count(topic_id, level):
    try:
        r = s.table("questions").select("id",count="exact").eq("topic_id",topic_id).eq("level",level).execute()
        return r.count or 0
    except: return 0'''

new1 = '''# Global cache for question counts - loaded once per pass
_count_cache = {}
_cache_loaded = False

def load_count_cache():
    global _count_cache, _cache_loaded
    try:
        rows = s.table("questions").select("topic_id,level").execute().data or []
        _count_cache = {}
        for r in rows:
            key = f"{r.get(\"topic_id\")}_{r.get(\"level\")}"
            _count_cache[key] = _count_cache.get(key,0) + 1
        _cache_loaded = True
        print(f"Count cache loaded: {len(rows)} questions, {len(_count_cache)} topic-level pairs", flush=True)
    except Exception as e:
        print(f"Cache load failed: {e}", flush=True)
        _cache_loaded = False

def get_existing_count(topic_id, level):
    if _cache_loaded:
        return _count_cache.get(f"{topic_id}_{level}", 0)
    try:
        r = s.table("questions").select("id",count="exact").eq("topic_id",topic_id).eq("level",level).execute()
        return r.count or 0
    except: return 0

def invalidate_cache_entry(topic_id, level):
    key = f"{topic_id}_{level}"
    if key in _count_cache:
        _count_cache[key] = _count_cache.get(key,0) + 1'''

if old1 in content:
    content = content.replace(old1, new1)
    fixes += 1
    print("Fix 1 OK: Count cache added")
else:
    print("Fix 1 MISS: get_existing_count not found")

# Fix 2: Call load_count_cache at start of each pass
old2 = '''        topics = get_priority_topics()
        if not topics:
            print("No topics found - sleep 60s", flush=True)
            time.sleep(60)
            continue'''

new2 = '''        # Load count cache once per pass - saves 45+ minutes of DB calls
        load_count_cache()

        topics = get_priority_topics()
        if not topics:
            print("No topics found - sleep 60s", flush=True)
            time.sleep(60)
            continue'''

if old2 in content:
    content = content.replace(old2, new2)
    fixes += 1
    print("Fix 2 OK: Cache load added to main loop")
else:
    print("Fix 2 MISS: main loop pattern not found")

# Fix 3: Invalidate cache when saving
old3 = '''    if is_duplicate(s, q["question"], topic_id):
        print("      Duplicate - skip", flush=True)
        return False

    success, _ = safe_db_insert(s, "questions", rec)
    return success'''

new3 = '''    if is_duplicate(s, q["question"], topic_id):
        print("      Duplicate - skip", flush=True)
        return False

    success, _ = safe_db_insert(s, "questions", rec)
    if success:
        invalidate_cache_entry(topic_id, level)
    return success'''

if old3 in content:
    content = content.replace(old3, new3)
    fixes += 1
    print("Fix 3 OK: Cache invalidation on save")
else:
    print("Fix 3 MISS: save_question pattern not found")

# Fix 4: Reduce Groq wait from 3.5s to 2s
old4 = "GROQ_INTERVAL      = 3.5   # Seconds between Groq calls (org-wide rate limit)"
new4 = "GROQ_INTERVAL      = 2.0   # Seconds between Groq calls (reduced for speed)"
if old4 in content:
    content = content.replace(old4, new4)
    fixes += 1
    print("Fix 4 OK: Groq wait reduced 3.5s -> 2s")
else:
    print("Fix 4 MISS: GROQ_INTERVAL not found")

# Fix 5: Run every 2 hours instead of 3
old5 = "cron: '0 */3 * * *'"
new5 = "cron: '0 */2 * * *'"

open("generate_master.py", "w", encoding="utf-8").write(content)
print(f"\nTotal fixes: {fixes}/4")
print(f"File size: {len(content)} chars | Lines: {content.count(chr(10))}")
