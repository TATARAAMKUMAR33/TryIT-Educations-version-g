# Terminal Commands — TryIT Exam Generator
## Run these in order in your GitHub Codespace terminal

---

## STEP 1 — Setup (run once)

```bash
# Clone or navigate to your repo
cd your-repo-folder

# Install all dependencies
pip install -r requirements.txt

# Copy and fill in your credentials
cp .env.template .env
nano .env
# Fill in: SUPABASE_URL, SUPABASE_SERVICE_KEY, all 15 API keys
```

---

## STEP 2 — CHECK SUPABASE FIRST (most important)

```bash
# See exactly what tables exist in your Supabase right now
python supabase_inspect.py
```

**This will show:**
- ✅ Tables that exist (with row counts and columns)
- ❌ Tables that are missing
- 📋 What tables need to be created
- SQL to create missing tables

**After running, copy output and share with me — I'll tell you what to create.**

---

## STEP 3 — Create missing Supabase tables

```bash
# If tables are missing, run this to see the SQL
python exam_generator.py --dry-run --subcategory CBSE
# It will print the CREATE TABLE SQL — paste into Supabase SQL Editor
```

Or directly in Supabase Dashboard → SQL Editor → paste the SQL from db_inserter.py

---

## STEP 4 — Test with one subcategory first

```bash
# Dry run — generate but DON'T insert to Supabase
python exam_generator.py --dry-run --subcategory CBSE

# If output looks good, run for real
python exam_generator.py --subcategory CBSE

# Check what was inserted
python supabase_inspect.py
```

---

## STEP 5 — Run by phase (recommended for verification)

```bash
# Phase 1: Board Exams only
python exam_generator.py --phase 1

# Phase 2: Scholarships
python exam_generator.py --phase 2

# Phase 3: School Entrances
python exam_generator.py --phase 3

# ... verify each phase before running next
```

---

## STEP 6 — Run all (after you're confident)

```bash
# Run everything (will take many hours — use tmux to keep alive)
tmux new -s exam_gen
python exam_generator.py
# Ctrl+B then D to detach, tmux attach -t exam_gen to come back
```

---

## RESUME COMMANDS

```bash
# If script crashed or you stopped it
python exam_generator.py --resume

# Resume from specific subcategory
python exam_generator.py --subcategory GATE  # starts from GATE onward
```

---

## MONITORING COMMANDS

```bash
# Check API key status (usage, rate limits, cooldowns)
python exam_generator.py --status

# See what needs manual verification
python exam_generator.py --verify-only

# Check Supabase table row counts
python supabase_inspect.py

# Watch logs in real time (in second terminal)
watch -n 5 "python exam_generator.py --status"
```

---

## USEFUL SUPABASE QUERIES (run in Supabase SQL Editor)

```sql
-- How many exams generated total?
SELECT COUNT(*) FROM exams;

-- Count by category
SELECT category, COUNT(*) FROM exams GROUP BY category ORDER BY COUNT(*) DESC;

-- Count by state
SELECT state, COUNT(*) FROM exams GROUP BY state ORDER BY COUNT(*) DESC;

-- All low-confidence entries needing verification
SELECT exam_name, subcategory, confidence FROM exams 
WHERE confidence = 'LOW' OR needs_verification = true
ORDER BY subcategory;

-- Generation log — what's been done
SELECT subcategory, status, generated_count, inserted_count, created_at 
FROM generation_log ORDER BY created_at DESC LIMIT 50;

-- Verification queue — what YOU need to check
SELECT exam_name, subcategory, issues FROM verification_queue 
WHERE verified = false ORDER BY created_at;

-- Delete all generated data (reset)
TRUNCATE TABLE exams, generation_log, generation_progress, verification_queue;
```

---

## KEEP-ALIVE (prevent Codespace timeout)

```bash
# In a separate terminal, ping every 5 minutes to keep codespace alive
while true; do echo "alive $(date)"; sleep 300; done
```

---

## QUICK REFERENCE

| Command | What it does |
|---------|-------------|
| `python supabase_inspect.py` | **First thing to run** — shows all tables |
| `python exam_generator.py --dry-run --subcategory CBSE` | Test one, no insert |
| `python exam_generator.py --phase 1` | Run phase 1 only |
| `python exam_generator.py --resume` | Continue after crash |
| `python exam_generator.py --verify-only` | See flagged items |
| `python exam_generator.py --status` | API key health |
