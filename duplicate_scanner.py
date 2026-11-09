import os, requests
from datetime import datetime, timezone, timedelta

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}
hpost = {**h, 'Content-Type': 'application/json', 'Prefer': 'return=minimal'}

# Find same phone number duplicates
r = requests.get(
    f'{u}/rest/v1/profiles?select=email,phone,device_hash&phone=not.is.null',
    headers=h)
profiles = r.json() if r.ok else []

phone_map: dict = {}
for p in profiles:
    ph = p.get('phone','').replace(' ','').replace('-','')
    if ph:
        phone_map.setdefault(ph, []).append(p['email'])

inserted = 0
for phone, emails in phone_map.items():
    if len(emails) >= 2:
        for i in range(len(emails)):
            for j in range(i+1, len(emails)):
                requests.post(
                    f'{u}/rest/v1/duplicate_account_flags',
                    headers=hpost,
                    json={
                        'email_1': emails[i],
                        'email_2': emails[j],
                        'match_type': 'phone',
                        'match_score': 100,
                        'flagged_at': datetime.now(timezone.utc).isoformat()
                    })
                inserted += 1

print(f"Duplicate scanner complete. {inserted} new flags inserted.")