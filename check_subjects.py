import os, requests
from dotenv import load_dotenv
load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

r = requests.get(f'{u}/rest/v1/subjects?select=id,name&limit=500', headers=h).json()
print(f'Existing subjects: {len(r)}')
for s in r:
    sid = s.get('id','')
    sname = s.get('name','')
    print(f'  {sid}: {sname}')
