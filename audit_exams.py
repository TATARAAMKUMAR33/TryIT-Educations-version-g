import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

# Get all exams
exams = requests.get(f'{u}/rest/v1/exams?select=id,name,category,tiers&limit=500', headers=h).json()
print(f'Total exams in DB: {len(exams)}')
print()

from collections import defaultdict
by_category = defaultdict(list)
for e in exams:
    cat = e.get('category','unknown')
    by_category[cat].append(e)

print('=== EXAMS BY CATEGORY ===')
for cat, items in sorted(by_category.items()):
    print(f'\n{cat.upper()} ({len(items)} exams):')
    for e in items:
        tiers = e.get('tiers',[])
        tier_names = [t.get('tier','') for t in tiers] if tiers else []
        print(f'  - {e.get("id")}: {tier_names}')

# Check syllabus map coverage
maps = requests.get(f'{u}/rest/v1/exam_syllabus_map?select=exam_id,topic_id&limit=5000', headers=h).json()
print(f'\n=== SYLLABUS MAP ===')
print(f'Total mappings: {len(maps)}')
mapped_exams = set(m.get("exam_id") for m in maps)
mapped_topics = set(m.get("topic_id") for m in maps)
print(f'Exams with syllabus: {len(mapped_exams)}')
print(f'Topics mapped to exams: {len(mapped_topics)}')

# Find unmapped exams
unmapped = [e for e in exams if e.get("id") not in mapped_exams]
print(f'Exams WITHOUT syllabus map: {len(unmapped)}')
for e in unmapped[:20]:
    print(f'  MISSING: {e.get("id")}')
