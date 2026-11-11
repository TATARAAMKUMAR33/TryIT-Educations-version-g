import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json"}

# Test insert ONE mapping without ignore-duplicates
test = [{
    "map_id": "map_test_xyz123abc",
    "exam_id": "upsc_cse",
    "section_id": "upsc_cse_main",
    "topic_id": "cbse_maths_class10_trigonometry",
    "weightage_percent": 10,
    "priority": 1,
    "notes": "test"
}]
r = requests.post(f"{u}/rest/v1/exam_syllabus_map", headers=h, json=test, timeout=15)
print("Status:", r.status_code)
print("Response:", r.text[:300])
