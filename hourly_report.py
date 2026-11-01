import os, requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"

h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Prefer': 'count=exact', 'Range': '0-0'}
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

total = requests.get(f'{u}/rest/v1/questions?select=id', headers=h).headers.get('content-range').split('/')[-1]
v3_total = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3', headers=h).headers.get('content-range').split('/')[-1]
v3_today = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3&created_at=gte.{today}', headers=h).headers.get('content-range').split('/')[-1]

# Calculate next run time
now = datetime.now(timezone.utc)
next_run = (now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1))
time_until_next = next_run - now
mins_until = int(time_until_next.total_seconds() / 60)

msg = f'📊 <b>TRYIT DB STATUS</b>\n\n'
msg += f'📚 <b>Total Questions:</b> {total}\n'
msg += f'🚀 <b>Generated Today:</b> {v3_today}\n\n'
msg += f'⏰ <b>Next Run:</b> {next_run.strftime("%H:%M")} UTC\n'
msg += f'(In {mins_until} minutes)\n\n'

url = f'https://api.telegram.org/bot{tg_token}/sendMessage'
payload = {'chat_id': tg_chat, 'text': msg, 'parse_mode': 'HTML'}
requests.post(url, json=payload)
print('Telegram Report Sent!')
