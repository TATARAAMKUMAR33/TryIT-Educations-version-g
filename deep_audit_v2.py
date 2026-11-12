"""
deep_audit_v2.py - Complete system audit + identify why generation is slow
"""
import os, requests
from dotenv import load_dotenv
from collections import Counter
load_dotenv()

u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}"}

def cnt(url):
    try:
        cr = requests.get(url, headers={**h,"Prefer":"count=exact","Range":"0-0"},
                         timeout=15).headers.get("content-range","?").split("/")[-1]
        return cr
    except: return "?"

print("="*60)
print("DEEP AUDIT v2")
print("="*60)

# ── CORE COUNTS ───────────────────────────────────────────────────
print("\n📊 CORE COUNTS")
print(f"  Topics:        {cnt(f'{u}/rest/v1/topics?select=id')}")
print(f"  Subjects:      {cnt(f'{u}/rest/v1/subjects?select=subject_id')}")
print(f"  Exams (table): {cnt(f'{u}/rest/v1/exams?select=id')}")
print(f"  Exam Registry: {cnt(f'{u}/rest/v1/exam_registry?select=exam_id')}")
print(f"  Syllabus Maps: {cnt(f'{u}/rest/v1/exam_syllabus_map?select=map_id')}")
print(f"  Questions:     {cnt(f'{u}/rest/v1/questions?select=id')}")

# ── QUESTIONS BY LEVEL ────────────────────────────────────────────
print("\n📊 QUESTIONS BY LEVEL")
q_rows = requests.get(f"{u}/rest/v1/questions?select=level,generated_by&limit=5000",
                     headers=h).json()
lc = Counter(r.get("level") for r in q_rows if isinstance(r,dict))
vc = Counter(r.get("generated_by") for r in q_rows if isinstance(r,dict))
total_q = sum(lc.values())
for l in range(1,11):
    c = lc.get(l,0)
    pct = c/total_q*100 if total_q else 0
    bar = "█"*min(25,c//20)
    target = 30 if l<=3 else 20 if l<=6 else 15 if l==7 else 10 if l<=9 else 5
    status = "✅" if c >= target*10 else "⚠️" if c > 0 else "❌"
    print(f"  L{l:2d}: {c:5d} ({pct:4.1f}%) {bar} {status}")

print(f"\n📊 BY ENGINE")
for eng, c in sorted(vc.items(), key=lambda x:-x[1]):
    print(f"  {eng}: {c}")

# ── TOPIC COVERAGE ────────────────────────────────────────────────
print("\n📊 TOPIC COVERAGE")
all_topics = requests.get(f"{u}/rest/v1/topics?select=topic_id,subject_id,difficulty_range&limit=2000",
                         headers=h).json()
q_topic_rows = requests.get(f"{u}/rest/v1/questions?select=topic_id,level&limit=5000",
                            headers=h).json()
topic_q_count = Counter(r.get("topic_id") for r in q_topic_rows if isinstance(r,dict))
zero_topics = [t for t in all_topics if topic_q_count.get(t["topic_id"],0)==0]
print(f"  Total topics:            {len(all_topics)}")
print(f"  Topics WITH questions:   {len(all_topics)-len(zero_topics)}")
print(f"  Topics with 0 questions: {len(zero_topics)}")

# Zero topics by subject
zero_by_subj = Counter(t.get("subject_id") for t in zero_topics)
print(f"\n  Top subjects with 0-Q topics:")
for subj, c in sorted(zero_by_subj.items(), key=lambda x:-x[1])[:20]:
    print(f"    {subj}: {c} topics")

# ── WHY GENERATION IS SLOW ────────────────────────────────────────
print("\n⚠️  GENERATION ANALYSIS")

# Check topics per tier
TIER_MAP = {
    1:["cbse","icse_board","tn_state","mh_state","ap_ts","karnataka","up_state",
       "bihar","wb_state","gujarat","punjab","rajasthan","mp_state","kerala",
       "odisha","assam","nep_school","cbse_maths","cbse_science","cbse_sst",
       "cbse_physics","cbse_chemistry","cbse_biology"],
    2:["ug_pg_entrances"],
    3:["gate_prep","mba_cat","medical_pg"],
    4:["research_academia"],
    5:["study_abroad","international_exams","french","german","spanish","japanese","mandarin","korean","arabic"],
    6:["competitive_govt","ssc_exams","rrb_exams","bank_exams","defence_exams","upsc_mains","state_police","banking_extended","psu_engineering","revenue_civil","ctet_teaching","state_tet"],
    7:["state_exams","tamil_full","telugu_full","kannada_full","malayalam_full",
       "marathi_full","bengali_full","gujarati_full","punjabi_full","agriculture_extended",
       "judicial_exams","health_extended"],
    8:["ca_cs_cma","ca_final","finance_cert","law_practice","usmle","nursing",
       "pharmacy","intl_medical","cloud_cert","security_cert","project_mgmt",
       "data_cert","salesforce","aptitude_corp","campus_place","nclex","gulf_medical"],
}

tier_counts = {i:0 for i in range(1,9)}
for t in all_topics:
    sid = t.get("subject_id","")
    for tier, pats in TIER_MAP.items():
        if any(p in sid for p in pats):
            tier_counts[tier] += 1
            break
    else:
        tier_counts[6] += 1  # default to tier 6

print("  Topics by tier:")
for tier, count in tier_counts.items():
    tier_names = {1:"School",2:"UG Entry",3:"PG/GATE",4:"PhD",
                  5:"Foreign",6:"Govt/Corp",7:"State/Lang",8:"Professional"}
    print(f"    T{tier} {tier_names[tier]}: {count} topics")

# ── IDENTIFY BOTTLENECKS ──────────────────────────────────────────
print("\n⚠️  BOTTLENECK ANALYSIS")
print("""
  ISSUE 1: 1,573 topics but only 37 have questions
  → Engine processes 3 workers × 1 topic at a time
  → Each topic takes 3-5 minutes (Groq rate limit waits)
  → 113 min run / 4 min per topic = ~28 topics per run
  → Need 1,573/28 = 56 runs to cover all topics ONCE

  ISSUE 2: Groq 1,000 RPD org-wide is the ceiling
  → 1,000 calls × 7 Q = 7,000 Q max from Groq per day
  → 8 runs/day × 125 calls per run = 1,000 Groq calls used
  → Each run = 125 Groq calls + 250 Gemini calls = 375 total

  ISSUE 3: Topics with L1-L7 need 165 Q each
  → 1,573 × 165 = 259,545 Q needed
  → At 15,000/day = 17 days to complete all topics

  FIX NEEDED:
  → Increase Gemini keys (free tier = 500 RPD each)
  → Add 5 more Gemini accounts = 2,500 more calls/day
  → That gives 4,500 more Q/day = 19,500 Q/day total
""")

# ── WORK REMAINING ────────────────────────────────────────────────
print("📊 WORK REMAINING")
total_needed = 0
for t in all_topics:
    dr = t.get("difficulty_range","2-7")
    try: lo,hi = map(int,dr.split("-"))
    except: lo,hi = 2,7
    for lvl in range(lo,hi+1):
        if lvl<=3: total_needed+=30
        elif lvl<=6: total_needed+=20
        elif lvl==7: total_needed+=15
        elif lvl<=9: total_needed+=10
        else: total_needed+=5

have = int(cnt(f"{u}/rest/v1/questions?select=id")) if cnt(f"{u}/rest/v1/questions?select=id").isdigit() else 0
remaining = total_needed - have
print(f"  Total questions needed: {total_needed:,}")
print(f"  Questions in DB:        {have:,}")
print(f"  Remaining:              {remaining:,}")
print(f"  At current 1,600/run:   {remaining//1600} runs = {remaining//1600//8} days")
print(f"  At target 3,000/run:    {remaining//3000} runs = {remaining//3000//8} days")
print(f"  At ideal 15,000/day:    {remaining//15000} days")

print("\n✅ WHAT TO FIX FOR 3,000+/RUN")
print("""
  1. Add 5 more Gemini API keys (free accounts)
     → Each adds 500 RPD = 3,500 more Q/day
  2. Fix Groq wait: reduce 3.5s to 2s between calls
     → Saves 90 seconds per run = 45 more Groq calls
  3. Run every 2 hours instead of 3 hours
     → 12 runs/day instead of 8 = 50% more output
  4. Skip topics already at target, focus on 0-Q topics
     → Engine already does this but with 1,573 topics
        it spends too much time checking existing counts
""")
print("="*60)
