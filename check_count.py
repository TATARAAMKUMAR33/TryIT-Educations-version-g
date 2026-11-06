import os, requests
from dotenv import load_dotenv
from datetime import datetime, timezone
load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
def count(url):
    try:
        cr = requests.get(url, headers={**h,'Prefer':'count=exact','Range':'0-0'}, timeout=10).headers.get('content-range','0/0')
        return cr.split('/')[-1]
    except: return '?'
print('Total all time:', count(f'{u}/rest/v1/questions?select=id'))
print('Today total:   ', count(f'{u}/rest/v1/questions?select=id&created_at=gte.{today}'))
print('v7 today:      ', count(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7&created_at=gte.{today}'))
