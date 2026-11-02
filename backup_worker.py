import os, requests, json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

print("💾 Running Database Backup...")
tables = ['questions', 'tickets', 'users', 'staff_roles', 'invoices']
backup_data = {}

for table in tables:
    try:
        res = requests.get(f'{u}/rest/v1/{table}?select=*', headers=h)
        backup_data[table] = res.json()
        print(f"  ✅ Backed up {table}: {len(res.json())} rows")
    except:
        print(f"  ❌ Failed to backup {table}")

# Save to a local file (Cloudflare R2 upload held as requested)
filename = f"backup_{datetime.now().strftime('%Y%m%d')}.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(backup_data, f, indent=2)

print(f"✅ Backup saved locally as {filename}")
# TODO: Add Cloudflare R2 Upload logic here later.
