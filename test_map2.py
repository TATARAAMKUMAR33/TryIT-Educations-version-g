import os, requests, uuid, time
from dotenv import load_dotenv
load_dotenv()

u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")

# Use upsert instead of ignore-duplicates
h = {
    "apikey": k,
    "Authorization": f"Bearer {k}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

# Test one insert with a known-good exam_id from exam_registry
# First get a real exam_id from registry
r = requests.get(f"{u}/rest/v1/exam_registry?select=exam_id&limit=3", headers=h)
reg_exams = [x["exam_id"] for x in r.json()]
print("Registry sample:", reg_exams)

# Get real topic_id
r2 = requests.get(f"{u}/rest/v1/topics?select=topic_id&limit=1", headers=h)
real_topic = r2.json()[0]["topic_id"]
print("Topic sample:", real_topic)

# Test insert
test = [{
    "map_id": f"map_{uuid.uuid4().hex[:12]}",
    "exam_id": reg_exams[0],
    "section_id": f"{reg_exams[0]}_main",
    "topic_id": real_topic,
    "weightage_percent": 20,
    "priority": 1,
    "notes": "test_v2"
}]
r3 = requests.post(f"{u}/rest/v1/exam_syllabus_map", headers=h, json=test, timeout=30)
print(f"Test insert: {r3.status_code}")
print(f"Response: {r3.text[:200]}")
