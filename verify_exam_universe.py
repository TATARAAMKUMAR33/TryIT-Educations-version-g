import os
from collections import Counter
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 75)
print("🔍 EXAM UNIVERSE INVENTORY & RATE REPORT")
print("=" * 75)

# 1. TOTAL COUNTS
total_exams = s.table('exams').select('id', count='exact').execute().count
flagged = s.table('exams').select('id', count='exact').eq('needs_verification', True).execute().count
verified = total_exams - flagged

print(f"📊 TOTAL EXAMS IN DATABASE: {total_exams}")
print(f"✅ Verified (Passed Gemini): {verified}")
print(f"⚠️  Flagged (Needs Review):   {flagged}")

# 2. RATE CALCULATION (Exams created in the last 1 hour)
one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
recent = s.table('exams').select('id').gte('generated_at', one_hour_ago).execute().data
recent_count = len(recent)
print(f"\n⏱️  RATE: {recent_count} exams generated in the last 1 hour.")
if recent_count > 0:
    print(f"   (If this rate was sustained: {recent_count * 24} exams/day)")

# 3. BREAKDOWN BY CATEGORY
all_exams = s.table('exams').select('category').execute().data
cats = Counter(e['category'] for e in all_exams if e.get('category'))
print("\n📁 BREAKDOWN BY CATEGORY:")
for cat, count in cats.most_common(15):
    print(f"   • {cat.replace('_', ' ').title():<25} : {count} exams")

# 4. RECENT GENERATION LOGS
print("\n📋 RECENT GENERATION LOGS (Last 5):")
logs = s.table('generation_log').select('subcategory, status, generated_count, inserted_count, created_at').order('created_at', desc=True).limit(5).execute().data
for log in logs:
    time_str = log['created_at'][:19].replace('T', ' ')
    print(f"   [{time_str}] {log['subcategory']}: Gen={log['generated_count']}, Saved={log['inserted_count']} ({log['status']})")

# 5. DEEP INSPECTION OF THE LATEST EXAM
print("\n" + "=" * 75)
print("🕵️‍♂️ DEEP INSPECTION: MOST RECENT EXAM GENERATED")
print("=" * 75)
latest_exam = s.table('exams').select('*').order('generated_at', desc=True).limit(1).execute().data

if latest_exam:
    e = latest_exam[0]
    print(f"Exam Name : {e.get('name')}")
    print(f"Body      : {e.get('conducting_body')}")
    print(f"Category  : {e.get('category')} -> {e.get('subcategory')}")
    print(f"Confidence: {e.get('confidence')}")
    print(f"Needs Rev : {e.get('needs_verification')}")
    
    print("\n💾 STAGES/PAPERS (JSONB):")
    tiers = e.get('tiers', [])
    if isinstance(tiers, list):
        for t in tiers:
            print(f"  - {t.get('tier')}: {t.get('q')} Qs, {t.get('marks')} Marks, {t.get('time')} min")
            if t.get('subjects'):
                for subj in t.get('subjects')[:3]:
                    print(f"      * {subj.get('name')} ({subj.get('weightage')}%)")
    else:
        print(f"  {tiers}")

    print("\n📉 CUTOFFS (JSONB):")
    print(f"  {e.get('cutoffs')}")

    print("\n🎓 ELIGIBILITY (JSONB):")
    print(f"  {e.get('eligibility')}")
else:
    print("⚠️ No exams found in the database yet.")

print("\n" + "=" * 75)
