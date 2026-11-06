import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

# Get one subject to see structure
r = requests.get(f'{u}/rest/v1/subjects?limit=5', headers=h)
print('Status:', r.status_code)
print('Response:', r.text[:500])
