import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}"}

# Get exam_registry structure and sample
r = requests.get(f"{u}/rest/v1/exam_registry?limit=5", headers=h)
print("Status:", r.status_code)
print("Sample:", r.text[:500])

# Count
r2 = requests.get(f"{u}/rest/v1/exam_registry?select=id",
    headers={**h,"Prefer":"count=exact","Range":"0-0"})
print("Total in exam_registry:", r2.headers.get("content-range","?").split("/")[-1])
