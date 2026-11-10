"""
Full system audit - checks everything before running v8
"""
import os, requests
from dotenv import load_dotenv
from collections import Counter, defaultdict
load_dotenv()

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

print("="*60)
print("TRYIT COMPLETE SYSTEM AUDIT")
print("="*60)

# 1. TOPICS
topics = requests.get(f'{u}/rest/v1/topics?select=topic_id,subject_id,difficulty_range,is_visual,launch_phase&limit=2000', headers=h).json()
print(f"\n1. TOPICS")
print(f"   Total topics: {len(topics)}")
phase_counts = Counter(t.get('launch_phase') for t in topics)
for p,c in sorted(phase_counts.items()):
    print(f"   {p}: {c}")
visual = sum(1 for t in topics if t.get('is_visual'))
print(f"   Visual topics (need diagrams): {visual}")
print(f"   Text-only topics: {len(topics)-visual}")

# 2. SUBJECTS
subjects = requests.get(f'{u}/rest/v1/subjects?select=subject_id,subject_name&limit=500', headers=h).json()
print(f"\n2. SUBJECTS")
print(f"   Total subjects: {len(subjects)}")

# 3. EXAMS
exams = requests.get(f'{u}/rest/v1/exams?select=id,category&limit=1000', headers=h).json()
print(f"\n3. EXAMS")
print(f"   Total exams: {len(exams)}")
exam_cats = Counter(e.get('category') for e in exams)
for cat,cnt in sorted(exam_cats.items(), key=lambda x:-x[1]):
    print(f"   {cat}: {cnt}")

# 4. SYLLABUS MAP
maps = requests.get(f'{u}/rest/v1/exam_syllabus_map?select=exam_id,topic_id&limit=5000', headers=h).json()
print(f"\n4. SYLLABUS MAP")
print(f"   Total mappings: {len(maps)}")
mapped_exams  = set(m.get('exam_id') for m in maps)
mapped_topics = set(m.get('topic_id') for m in maps)
print(f"   Exams with mapping: {len(mapped_exams)}")
print(f"   Topics mapped to exams: {len(mapped_topics)}")
unmapped_exams  = len(exams) - len(mapped_exams)
unmapped_topics = len(topics) - len(mapped_topics)
print(f"   Exams WITHOUT mapping: {unmapped_exams}")
print(f"   Topics WITHOUT mapping: {unmapped_topics}")

# 5. QUESTIONS
q_count = requests.get(f'{u}/rest/v1/questions?select=id',
    headers={**h,'Prefer':'count=exact','Range':'0-0'}, timeout=10)
total_q = q_count.headers.get('content-range','?').split('/')[-1]
print(f"\n5. QUESTIONS IN DB")
print(f"   Total: {total_q}")

# Level breakdown
level_rows = requests.get(f'{u}/rest/v1/questions?select=level&limit=5000', headers=h).json()
lc = Counter(r.get('level') for r in level_rows if isinstance(r,dict))
print(f"   By level:")
for l in range(1,11):
    count = lc.get(l,0) or lc.get(str(l),0)
    bar = '#' * min(30, count//50)
    print(f"   L{l}: {count:>6} {bar}")

# 6. TOPICS WITH ZERO QUESTIONS
q_topics = set(r.get('topic_id') for r in requests.get(
    f'{u}/rest/v1/questions?select=topic_id&limit=5000', headers=h).json()
    if isinstance(r,dict))
zero_q_topics = [t for t in topics if t.get('topic_id') not in q_topics]
print(f"\n6. TOPICS WITH ZERO QUESTIONS: {len(zero_q_topics)}")
# Show by subject
zero_by_subj = Counter(t.get('subject_id') for t in zero_q_topics)
for subj, cnt in sorted(zero_by_subj.items(), key=lambda x:-x[1])[:20]:
    print(f"   {subj}: {cnt} topics with 0 questions")

# 7. MISSING CRITICAL EXAMS CHECK
print(f"\n7. CRITICAL EXAM COVERAGE CHECK")
critical_exams = [
    'upsc_cse','ssc_cgl','jee_main','neet_ug','gate','ibps_po',
    'tnpsc','ntse','ielts','ca_foundation','ugc_net','clat',
    'nda','rrb_ntpc','ssc_chsl','cbse_class_10','cbse_class_12'
]
exam_ids = set(e.get('id') for e in exams)
for ce in critical_exams:
    found = any(ce in eid for eid in exam_ids)
    mapped = any(ce in eid for eid in mapped_exams)
    status = "OK+MAPPED" if mapped else ("EXISTS" if found else "MISSING")
    print(f"   {ce}: {status}")

# 8. GENERATE_MASTER.PY CHECKS
print(f"\n8. GENERATE_MASTER.PY CHECKS")
try:
    gm = open('generate_master.py', encoding='utf-8').read()
    checks = {
        'Version v8':           'VERSION: 8.0' in gm,
        'Gemini REST (no SDK)': 'generativelanguage.googleapis.com' in gm,
        'Groq rate limiter':    'groq_rate_wait' in gm,
        'Tier priority':        'get_tier' in gm,
        'Level targets 30/20':  'get_target' in gm,
        'Batch size 7':         'BATCH_SIZE         = 7' in gm,
        'Exam syllabus map':    'get_exam_info' in gm,
        'NVIDIA L8-10 only':    'level >= 8' in gm,
        'All phases included':  'phase_2_2027' in gm,
        'SambaNova removed':    'SambaNova' not in gm.split('def ')[0],
    }
    for check, result in checks.items():
        status = "PASS" if result else "FAIL"
        print(f"   {check}: {status}")
except FileNotFoundError:
    print("   generate_master.py NOT FOUND in current directory")

# 9. COVERAGE GAPS
print(f"\n9. WHAT'S STILL MISSING")

# Check for key subject gaps
expected_subjects = [
    'python_programming','javascript_programming','dsa_algorithms',
    'cbse_maths','cbse_science','tn_state_board','mh_state_board',
    'gate_prep','ca_cs_cma','french_language','study_abroad_usa',
    'cybersecurity','data_science_ml','generative_ai','cloud_devops',
    'tamil_full','telugu_full','kannada_full','personal_finance',
    'entrepreneurship','soft_skills','digital_marketing',
]
subj_ids = set(s.get('subject_id') for s in subjects)
for exp in expected_subjects:
    status = "OK" if exp in subj_ids else "MISSING"
    if status == "MISSING":
        print(f"   MISSING SUBJECT: {exp}")

print(f"\n   Subjects present: {len(subj_ids)}")
missing_count = sum(1 for e in expected_subjects if e not in subj_ids)
print(f"   Missing from expected list: {missing_count}")

# 10. TOTAL QUESTIONS NEEDED
print(f"\n10. TOTAL WORK REMAINING")
total_needed = 0
for t in topics:
    dr = t.get('difficulty_range','2-7')
    try: lo,hi = map(int,dr.split('-'))
    except: lo,hi = 2,7
    for lvl in range(lo, hi+1):
        if lvl<=3: target=30
        elif lvl<=6: target=20
        elif lvl==7: target=15
        elif lvl<=9: target=10
        else: target=5
        total_needed += target

total_have = int(total_q) if total_q.isdigit() else 0
remaining = total_needed - total_have
print(f"   Total questions needed: {total_needed:,}")
print(f"   Questions in DB now:    {total_have:,}")
print(f"   Remaining to generate:  {remaining:,}")
print(f"   At 12,000/day:          {remaining//12000} days")
print(f"   At 15,000/day:          {remaining//15000} days")

print(f"\n{'='*60}")
print("AUDIT COMPLETE")
print("="*60)