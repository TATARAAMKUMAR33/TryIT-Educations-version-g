import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}

# Check what exam_ids actually exist in exams table
exams = requests.get(f"{u}/rest/v1/exams?select=id&limit=5", headers=h).json()
print("Sample exam IDs in DB:")
for e in exams:
    print(f"  {e.get('id')}")

# Check what topic_ids exist
topics = requests.get(f"{u}/rest/v1/topics?select=topic_id&limit=5", headers=h).json()
print("Sample topic IDs in DB:")
for t in topics:
    print(f"  {t.get('topic_id')}")

# Check exam_syllabus_map columns
maps = requests.get(f"{u}/rest/v1/exam_syllabus_map?limit=2", headers=h).json()
print("Sample map rows:")
for m in maps:
    print(f"  {m}")

# Try insert ONE mapping with real IDs
real_exam = exams[0].get("id") if exams else None
real_topic = topics[0].get("topic_id") if topics else None
print(f"\nTrying insert: exam={real_exam} topic={real_topic}")
test = [{
    "map_id": "map_test_fix_xyz999",
    "exam_id": real_exam,
    "section_id": f"{real_exam}_main",
    "topic_id": real_topic,
    "weightage_percent": 10,
    "priority": 1,
    "notes": "test fix"
}]
r = requests.post(f"{u}/rest/v1/exam_syllabus_map", headers=h, json=test, timeout=15)
print("Status:", r.status_code)
print("Response:", r.text[:200])
