import os, requests
from dotenv import load_dotenv
load_dotenv()

print("="*55)
print("KEY STATUS CHECK")
print("="*55)

# Groq keys
groq_keys = []
for i in range(1,6):
    k = os.getenv(f"GROQ_API_KEY_{i}") or os.getenv("GROQ_API_KEY")
    if k and k not in groq_keys: groq_keys.append(k)

print(f"\nGroq keys found: {len(groq_keys)}")
for i,k in enumerate(groq_keys):
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},
            json={"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"hi"}],"max_tokens":5},
            timeout=15)
        status = "OK" if r.status_code==200 else f"ERR {r.status_code}"
        print(f"  Groq key {i+1}: {status}")
    except Exception as e:
        print(f"  Groq key {i+1}: TIMEOUT/ERR {str(e)[:40]}")

# Gemini keys
gemini_keys = []
for i in range(1,6):
    k = os.getenv(f"GEMINI_API_KEY_{i}") or os.getenv("GEMINI_API_KEY")
    if k and k not in gemini_keys: gemini_keys.append(k)

print(f"\nGemini keys found: {len(gemini_keys)}")
for i,k in enumerate(gemini_keys):
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={k}",
            json={"contents":[{"parts":[{"text":"hi"}]}]},
            timeout=15)
        if r.status_code==200:
            status = "OK -> gemini-3.5-flash"
        else:
            # Try gemini-1.5-flash
            r2 = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={k}",
                json={"contents":[{"parts":[{"text":"hi"}]}]},
                timeout=15)
            status = f"gemini-3.5-flash:{r.status_code} | gemini-1.5-flash:{r2.status_code}"
        print(f"  Gemini key {i+1}: {status}")
    except Exception as e:
        print(f"  Gemini key {i+1}: ERR {str(e)[:50]}")

# NVIDIA keys
nvidia_keys = []
for i in range(1,6):
    k = os.getenv(f"NVIDIA_API_KEY_{i}") or os.getenv("NVIDIA_API_KEY")
    if k and k not in nvidia_keys: nvidia_keys.append(k)

print(f"\nNVIDIA keys found: {len(nvidia_keys)}")
for i,k in enumerate(nvidia_keys):
    try:
        r = requests.post("https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},
            json={"model":"nvidia/nemotron-3-ultra-550b-a55b",
                  "messages":[{"role":"user","content":"hi"}],"max_tokens":5},
            timeout=20)
        status = "OK" if r.status_code==200 else f"ERR {r.status_code}: {r.text[:60]}"
        print(f"  NVIDIA key {i+1}: {status}")
    except Exception as e:
        print(f"  NVIDIA key {i+1}: ERR {str(e)[:50]}")

print("\n" + "="*55)
print("TOPIC/EXAM ALIGNMENT CHECK")
print("="*55)

u = os.getenv("SUPABASE_URL")
sk = os.getenv("SUPABASE_KEY")
h = {"apikey":sk,"Authorization":f"Bearer {sk}"}

# Check if new topics are in DB
new_topic_ids = [
    "ctet_child_development_p1","tn_police_si","bhel_engineer",
    "rbi_grade_b_phase1","nclex_rn_complete","aws_saa_c03",
    "tcs_nqt_prep","civil_judge_state","aiims_staff_nurse"
]
print("\nNew topic verification:")
for tid in new_topic_ids:
    r = requests.get(f"{u}/rest/v1/topics?topic_id=eq.{tid}&select=topic_id,difficulty_range",
                    headers=h, timeout=10).json()
    status = f"OK (dr={r[0].get('difficulty_range')})" if r else "MISSING"
    print(f"  {tid}: {status}")

# Check syllabus map coverage for new topics
print("\nSyllabus map for new topics:")
for tid in new_topic_ids[:5]:
    r = requests.get(f"{u}/rest/v1/exam_syllabus_map?topic_id=eq.{tid}&select=exam_id&limit=3",
                    headers=h, timeout=10).json()
    exams = [x.get("exam_id") for x in r]
    print(f"  {tid}: {exams if exams else 'NO MAPPING'}")

# Check why v8 only generated 4 questions
print("\nv8 questions sample:")
r = requests.get(f"{u}/rest/v1/questions?generated_by=eq.tryit_v8&select=topic_id,level&limit=10",
                headers=h, timeout=10).json()
for q in r:
    print(f"  topic={q.get('topic_id')} L{q.get('level')}")
