import os, requests
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json', 'Prefer': 'resolution=merge-duplicates'}

print("🏥 Running Integration Health Monitor...")

# 1. Check Supabase
try:
    res = requests.get(f'{u}/rest/v1/', headers=h, timeout=5)
    sb_status = 'operational' if res.status_code in [200, 404] else 'outage'
except:
    sb_status = 'outage'

# 2. Check Telegram API
try:
    res = requests.get(f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/getMe", timeout=5)
    tg_status = 'operational' if res.status_code == 200 else 'degraded'
except:
    tg_status = 'outage'

# 3. Save to DB
requests.post(f"{u}/rest/v1/integration_status", headers=h, json=[
    {'service_name': 'Supabase', 'status': sb_status},
    {'service_name': 'Telegram API', 'status': tg_status}
])

print(f"Supabase: {sb_status} | Telegram: {tg_status}")
