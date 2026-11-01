import os
from collections import Counter
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 75)
print("📋 EXAM UNIVERSE VERIFICATION REPORT")
print("=" * 75)

# 1. TOTAL COUNTS
exams = s.table('exam_registry').select('exam_id').execute().data
tiers = s.table('exam_tiers').select('tier_id').execute().data
sections = s.table('exam_sections').select('section_id').execute().data
maps = s.table('exam_syllabus_map').select('map_id').execute().data

print(f"📊 TOTAL EXAMS REGISTERED:  {len(exams):,}")
print(f"📊 TOTAL TIERS/PAPERS:      {len(tiers):,}")
print(f"📊 TOTAL SECTIONS:          {len(sections):,}")
print(f"📊 TOTAL SYLLABUS MAPPINGS: {len(maps):,}\n")

# 2. BREAKDOWN BY CATEGORY
print("📁 EXAMS BY CATEGORY:")
cat_data = s.table('exam_registry').select('category').execute().data
categories = Counter(row['category'] for row in cat_data if row['category'])

for cat, count in categories.most_common():
    print(f"   - {cat.replace('_', ' ').title():<25} : {count} exams")

# 3. CHECK FOR SPECIFIC GRANULAR EXAMS (From your draft)
print("\n🔍 CHECKING SPECIFIC GRANULAR EXAMS:")
targets = ["MBA", "AYUSH", "SWAYAM", "NPTEL", "Agniveer", "Geospatial", "Executive MBA", "Distance MBA"]
all_exam_names = [e['exam_name'].lower() for e in s.table('exam_registry').select('exam_name').execute().data]

for target in targets:
    found = any(target.lower() in name for name in all_exam_names)
    if found:
        print(f"   ✅ Found: {target}")
    else:
        print(f"   ❌ MISSING: {target}")

# 4. SHOW THE 10 MOST RECENTLY ADDED EXAMS
print("\n🆕 10 MOST RECENTLY ADDED EXAMS:")
recent = s.table('exam_registry').select('exam_name, category').order('exam_id', desc=True).limit(10).execute().data
for r in recent:
    print(f"   - {r['exam_name']} ({r['category']})")

print("\n" + "=" * 75)
