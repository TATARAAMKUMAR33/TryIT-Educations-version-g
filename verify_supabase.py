"""
TryIT Question Bank — Supabase Verification
Checks: structure, topic mapping, exam tags, quality, duplicates, recent activity
"""
import os
from collections import Counter, defaultdict
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("🔍 TRYIT QUESTION BANK — FULL VERIFICATION REPORT")
print("=" * 70)

# ── 1. TOTAL COUNT ──
total = s.table('questions').select('id', count='exact').execute().count
print(f"\n📊 TOTAL QUESTIONS: {total}")

if total == 0:
    print("❌ No questions in database. Pipeline may not be saving.")
    exit()

# ── 2. FETCH ALL QUESTIONS ──
print("\n⏳ Fetching all questions for analysis...")
all_q = []
offset = 0
while True:
    batch = s.table('questions').select(
        'id, topic_id, subject_id, level, difficulty, question_en, options_en, '
        'correct_answer, explanation, exam_tags, quality_score, created_at, verified'
    ).range(offset, offset + 999).execute().data
    if not batch:
        break
    all_q.extend(batch)
    if len(batch) < 1000:
        break
    offset += 1000

print(f"✅ Fetched {len(all_q)} questions")

# ── 3. STRUCTURE CHECK ──
print("\n" + "─" * 70)
print("🔎 STRUCTURE VALIDATION")
print("─" * 70)

issues = {
    "missing_question": 0,
    "missing_options": 0,
    "wrong_option_count": 0,
    "invalid_correct_answer": 0,
    "missing_explanation": 0,
    "incomplete_explanation": 0,
    "missing_topic": 0,
    "missing_exam_tags": 0,
    "missing_level": 0,
    "duplicate_ids": 0,
}

EXPLANATION_KEYS = [
    "why_correct", "why_wrong_option_b", "why_wrong_option_c",
    "why_wrong_option_d", "story_explanation", "shortcut_tips",
    "cross_exam_intelligence"
]

question_texts = Counter()
sample_good = None

for q in all_q:
    # Question text
    if not q.get("question_en") or len(q["question_en"]) < 10:
        issues["missing_question"] += 1

    # Options
    opts = q.get("options_en")
    if not isinstance(opts, list):
        issues["missing_options"] += 1
    elif len(opts) != 4:
        issues["wrong_option_count"] += 1

    # Correct answer
    ca = q.get("correct_answer")
    if not isinstance(ca, int) or ca < 0 or ca > 3:
        issues["invalid_correct_answer"] += 1

    # Explanation
    expl = q.get("explanation")
    if not isinstance(expl, dict):
        issues["missing_explanation"] += 1
    else:
        missing_keys = [k for k in EXPLANATION_KEYS if not expl.get(k)]
        if missing_keys:
            issues["incomplete_explanation"] += 1
        elif sample_good is None:
            sample_good = q

    # Topic
    if not q.get("topic_id"):
        issues["missing_topic"] += 1

    # Exam tags
    et = q.get("exam_tags")
    if not et or not isinstance(et, list) or len(et) == 0:
        issues["missing_exam_tags"] += 1

    # Level
    if not isinstance(q.get("level"), int):
        issues["missing_level"] += 1

    # Duplicate text detection
    if q.get("question_en"):
        question_texts[q["question_en"][:100]] += 1

duplicates = sum(1 for text, count in question_texts.items() if count > 1)
issues["duplicate_ids"] = duplicates

for name, count in issues.items():
    icon = "✅" if count == 0 else ("⚠️" if count < 10 else "❌")
    print(f"  {icon} {name.replace('_', ' ').title():<30} {count}")

# ── 4. COVERAGE BY TOPIC ──
print("\n" + "─" * 70)
print("📚 COVERAGE BY TOPIC")
print("─" * 70)

topic_counts = Counter(q["topic_id"] for q in all_q if q.get("topic_id"))
print(f"  Topics with questions: {len(topic_counts)}")

print("\n  Top 10 topics:")
for tid, count in topic_counts.most_common(10):
    print(f"    {tid:<55} {count}")

# Topics still empty
all_topics = s.table('topics').select('topic_id').execute().data
all_topic_ids = set(t['topic_id'] for t in all_topics)
covered = set(topic_counts.keys())
empty = all_topic_ids - covered
print(f"\n  Empty topics: {len(empty)} / {len(all_topic_ids)}")
if empty:
    print("  First 5 empty:")
    for tid in list(empty)[:5]:
        print(f"    - {tid}")

# ── 5. COVERAGE BY LEVEL ──
print("\n" + "─" * 70)
print("📊 COVERAGE BY LEVEL")
print("─" * 70)

level_counts = Counter(q.get("level") for q in all_q if q.get("level"))
for lvl in sorted(level_counts.keys()):
    bar = "█" * min(50, level_counts[lvl] // 5)
    print(f"  L{lvl:>2}: {level_counts[lvl]:>5} {bar}")

# ── 6. COVERAGE BY EXAM ──
print("\n" + "─" * 70)
print("🎯 COVERAGE BY EXAM (via exam_tags)")
print("─" * 70)

exam_counts = Counter()
for q in all_q:
    for exam in (q.get("exam_tags") or []):
        exam_counts[exam] += 1

for exam, count in exam_counts.most_common(15):
    print(f"  {exam:<30} {count} questions")

# ── 7. QUALITY SCORE DISTRIBUTION ──
print("\n" + "─" * 70)
print("⭐ QUALITY SCORE DISTRIBUTION")
print("─" * 70)

score_counts = Counter(q.get("quality_score") for q in all_q if q.get("quality_score"))
for score in sorted(score_counts.keys(), reverse=True):
    print(f"  Score {score}: {score_counts[score]}")

# ── 8. RECENT ACTIVITY (last 60 min) ──
print("\n" + "─" * 70)
print("⏱️  RECENT ACTIVITY (last 60 minutes)")
print("─" * 70)

from datetime import datetime, timezone, timedelta
one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
recent = [q for q in all_q if q.get("created_at") and q["created_at"] >= one_hour_ago]
print(f"  Questions created in last hour: {len(recent)}")

if recent:
    print(f"  Rate: {len(recent)}/hour = {len(recent)*24}/day (if sustained)")
    print("\n  Last 5 created:")
    for q in sorted(recent, key=lambda x: x.get("created_at", ""), reverse=True)[:5]:
        print(f"    {q.get('created_at', '')[:19]} | {q.get('topic_id', '')[:40]} L{q.get('level')}")

# ── 9. SAMPLE QUESTION ──
print("\n" + "─" * 70)
print("📝 SAMPLE QUESTION (random)")
print("─" * 70)

if sample_good:
    print(f"  Topic: {sample_good.get('topic_id')}")
    print(f"  Level: {sample_good.get('level')}")
    print(f"  Difficulty: {sample_good.get('difficulty')}")
    print(f"  Exam tags: {sample_good.get('exam_tags')}")
    print(f"  Quality: {sample_good.get('quality_score')}")
    print(f"\n  Q: {sample_good.get('question_en', '')[:200]}")
    print(f"\n  Options:")
    for i, opt in enumerate(sample_good.get("options_en", [])):
        marker = "✅" if i == sample_good.get("correct_answer") else "  "
        print(f"    {marker} {i}. {opt[:80]}")
    print(f"\n  Explanation layers present:")
    for k in EXPLANATION_KEYS:
        val = sample_good.get("explanation", {}).get(k, "")
        print(f"    {'✅' if val else '❌'} {k}: {str(val)[:60]}...")

# ── 10. VERDICT ──
print("\n" + "=" * 70)
print("🏁 VERDICT")
print("=" * 70)

critical_issues = (
    issues["missing_question"] +
    issues["missing_options"] +
    issues["wrong_option_count"] +
    issues["invalid_correct_answer"] +
    issues["missing_explanation"] +
    issues["missing_topic"]
)

if critical_issues == 0 and len(recent) > 0:
    print("✅ HEALTHY — All questions valid, pipeline actively saving.")
elif critical_issues == 0:
    print("⚠️  VALID DATA but pipeline not active (no recent questions).")
elif critical_issues < 20:
    print(f"⚠️  MOSTLY HEALTHY — {critical_issues} minor issues found.")
else:
    print(f"❌ DATA ISSUES — {critical_issues} critical problems found.")

print("=" * 70)
