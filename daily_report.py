"""
Daily IST report — shows questions generated per hour in IST.
Usage: python3 daily_report.py            # Today IST
       python3 daily_report.py 2026-10-16 # Specific IST date
"""
import os, sys
from datetime import datetime, timezone, timedelta, date
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client

IST = timezone(timedelta(hours=5, minutes=30))
load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# Get target IST date
target = sys.argv[1] if len(sys.argv) > 1 else datetime.now(IST).strftime('%Y-%m-%d')
ist_date = date.fromisoformat(target)
print("=" * 70)
print(f"📊 DAILY REPORT — {target} (IST)")
print("=" * 70)

# Compute UTC range for this IST day
ist_start = datetime.combine(ist_date, datetime.min.time()).replace(tzinfo=IST)
ist_end = ist_start + timedelta(days=1)
utc_start = ist_start.astimezone(timezone.utc).isoformat()
utc_end = ist_end.astimezone(timezone.utc).isoformat()

print(f"\n⏰ IST window: {target} 00:00 – 23:59")
print(f"   UTC window: {utc_start[:19]} to {utc_end[:19]}")

# Fetch questions created in this window
print("\n⏳ Fetching questions from Supabase...")
all_q = []
offset = 0
while True:
    batch = s.table('questions').select(
        'id, topic_id, level, quality_score, exam_tags, created_at'
    ).gte('created_at', utc_start).lt('created_at', utc_end).range(offset, offset + 999).execute().data
    if not batch:
        break
    all_q.extend(batch)
    if len(batch) < 1000:
        break
    offset += 1000

print(f"✅ Found {len(all_q)} questions created on {target} (IST)")

if not all_q:
    print("\n⚠️  No questions in this window")
    sys.exit()

# Group by IST hour
hourly = Counter()
for q in all_q:
    dt_utc = datetime.fromisoformat(q['created_at'].replace('Z', '+00:00'))
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    dt_ist = dt_utc.astimezone(IST)
    hourly[dt_ist.hour] += 1

print("\n📈 HOURLY BREAKDOWN (IST):")
print("─" * 70)
for hour in range(24):
    count = hourly.get(hour, 0)
    bar = "█" * min(50, count // 3)
    if count > 0:
        print(f"  {hour:02d}:00 – {hour+1:02d}:00  {count:>4}  {bar}")

# Summary
print("\n" + "─" * 70)
print(f"📊 TOTAL: {len(all_q)} questions")
print(f"📈 RATE: {len(all_q)/24:.1f}/hour avg")

# Topics covered
topic_counts = Counter(q['topic_id'] for q in all_q)
print(f"\n📚 Topics covered: {len(topic_counts)}")
print("   Top 5:")
for tid, count in topic_counts.most_common(5):
    print(f"     {tid[:50]:<52} {count}")

# Exams covered
exam_counts = Counter()
for q in all_q:
    for exam in (q.get('exam_tags') or []):
        exam_counts[exam] += 1
print(f"\n🎯 Exams covered: {len(exam_counts)}")
for exam, count in exam_counts.most_common(5):
    print(f"     {exam:<20} {count}")

# Quality distribution
scores = Counter(q.get('quality_score') for q in all_q if q.get('quality_score'))
print(f"\n⭐ Quality distribution:")
for score in sorted(scores.keys(), reverse=True):
    print(f"     Score {score}: {scores[score]}")

print("\n" + "=" * 70)
