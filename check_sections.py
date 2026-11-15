import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}"}

# Check exam_sections structure
r = requests.get(f"{u}/rest/v1/exam_sections?limit=5", headers=h)
print("exam_sections sample:")
print(r.text[:500])

r2 = requests.get(f"{u}/rest/v1/exam_sections?select=section_id",
    headers={**h,"Prefer":"count=exact","Range":"0-0"})
print(f"Total sections: {r2.headers.get('content-range','?').split('/')[-1]}")
