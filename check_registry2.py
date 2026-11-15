import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {"apikey": k, "Authorization": f"Bearer {k}"}

# Get all exam_registry IDs
r = requests.get(f"{u}/rest/v1/exam_registry?select=exam_id,category&limit=1000", headers=h)
rows = r.json()
print(f"Total in exam_registry: {len(rows)}")
from collections import Counter
cats = Counter(row.get("category") for row in rows)
for cat, cnt in sorted(cats.items(), key=lambda x:-x[1]):
    print(f"  {cat}: {cnt}")
print("\nSample exam_ids:")
for row in rows[:10]:
    print(f"  {row.get('exam_id')}")
