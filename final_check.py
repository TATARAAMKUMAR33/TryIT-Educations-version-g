import os, requests
from dotenv import load_dotenv
from collections import Counter
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}"}

def count(url):
    try:
        cr = requests.get(url, headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=15).headers.get("content-range","0/0")
        return cr.split("/")[-1]
    except: return "?"

print("="*55)
print("TRYIT FINAL SYSTEM CHECK")
print("="*55)

# Core counts
print(f"\nTOPICS:        {count(f'{u}/rest/v1/topics?select=id')}")
print(f"SUBJECTS:      {count(f'{u}/rest/v1/subjects?select=subject_id')}")
print(f"EXAMS:         {count(f'{u}/rest/v1/exams?select=id')}")
print(f"EXAM REGISTRY: {count(f'{u}/rest/v1/exam_registry?select=exam_id')}")
print(f"SYLLABUS MAPS: {count(f'{u}/rest/v1/exam_syllabus_map?select=map_id')}")
print(f"QUESTIONS:     {count(f'{u}/rest/v1/questions?select=id')}")

# Questions by level
q_rows = requests.get(f"{u}/rest/v1/questions?select=level&limit=5000", headers=h).json()
lc = Counter(r.get("level") for r in q_rows if isinstance(r,dict))
print(f"\nBY LEVEL:")
for l in range(1,11):
    c = lc.get(l,0)
    bar = "#"*min(20,c//20)
    print(f"  L{l:2d}: {c:5d} {bar}")

# Questions by engine
for eng in ["tryit_v8","tryit_v7","tryit_v6"]:
    c = count(f"{u}/rest/v1/questions?select=id&generated_by=eq.{eng}")
    print(f"  {eng}: {c}")

# Topics with zero questions
all_topics = requests.get(f"{u}/rest/v1/topics?select=topic_id&limit=2000", headers=h).json()
q_topics   = set(r.get("topic_id") for r in requests.get(f"{u}/rest/v1/questions?select=topic_id&limit=5000", headers=h).json() if isinstance(r,dict))
zero = [t["topic_id"] for t in all_topics if t.get("topic_id") not in q_topics]
print(f"\nTopics with 0 questions: {len(zero)} / {len(all_topics)}")
print(f"Topics with questions:   {len(all_topics)-len(zero)} / {len(all_topics)}")

# Exam categories
exams = requests.get(f"{u}/rest/v1/exams?select=category&limit=1000", headers=h).json()
cats  = Counter(e.get("category") for e in exams)
print(f"\nEXAM CATEGORIES ({len(cats)} types, {len(exams)} total):")
for cat,cnt in sorted(cats.items(), key=lambda x:-x[1]):
    print(f"  {cat}: {cnt}")

# Work remaining
total_needed = 0
topics_full  = requests.get(f"{u}/rest/v1/topics?select=topic_id,difficulty_range&limit=2000", headers=h).json()
for t in topics_full:
    dr = t.get("difficulty_range","2-7")
    try: lo,hi = map(int,dr.split("-"))
    except: lo,hi = 2,7
    for lvl in range(lo,hi+1):
        if lvl<=3: total_needed+=30
        elif lvl<=6: total_needed+=20
        elif lvl==7: total_needed+=15
        elif lvl<=9: total_needed+=10
        else: total_needed+=5

have = int(count(f"{u}/rest/v1/questions?select=id")) if count(f"{u}/rest/v1/questions?select=id").isdigit() else 0
print(f"\nWORK REMAINING:")
print(f"  Total needed:    {total_needed:,}")
print(f"  Have now:        {have:,}")
print(f"  Remaining:       {total_needed-have:,}")
print(f"  At 12K/day:      {(total_needed-have)//12000} days")
print(f"  At 15K/day:      {(total_needed-have)//15000} days")
print("="*55)
