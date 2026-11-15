import os, requests, time
from dotenv import load_dotenv
load_dotenv()

u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}

print("🔄 Starting Bulk QA Reset...")

offset = 0
chunk_size = 1000
total_updated = 0

while True:
    # Fetch IDs that need updating
    r = requests.get(f'{u}/rest/v1/questions?select=id&or=(verified.eq.true,generated_by.neq.pending_review)&limit={chunk_size}', headers=h)
    if r.status_code != 200:
        print(f"Error fetching: {r.text}")
        break
        
    data = r.json()
    if not data:
        print("\n✅ All questions successfully updated!")
        break
        
    ids = [row['id'] for row in data]
    
    # Update this chunk
    ids_str = ",".join(ids)
    update_payload = {
        'verified': False,
        'generated_by': 'pending_review',
        'review_status': 'pending'
    }
    
    patch_res = requests.patch(f"{u}/rest/v1/questions?id=in.({ids_str})", headers=h, json=update_payload)
    
    if patch_res.status_code in [200, 204]:
        total_updated += len(ids)
        print(f"  ✅ Updated {total_updated} / 26,134 questions...")
    else:
        print(f"  ❌ Error updating chunk: {patch_res.text}")
        break
        
    time.sleep(0.5) # Prevent rate limiting

print(f"\n🎉 Finished. Total questions reset to Pending: {total_updated}")
