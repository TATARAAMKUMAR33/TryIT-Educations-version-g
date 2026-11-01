import os, requests
from collections import Counter, defaultdict
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"

h = {'apikey': k, 'Authorization': f'Bearer {k}'}
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

total = requests.get(f'{u}/rest/v1/questions?select=id', headers={**h, 'Prefer':'count=exact', 'Range':'0-0'}).headers.get('content-range').split('/')[-1]
v3_total = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3', headers={**h, 'Prefer':'count=exact', 'Range':'0-0'}).headers.get('content-range').split('/')[-1]
v3_today = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3&created_at=gte.{today}', headers={**h, 'Prefer':'count=exact', 'Range':'0-0'}).headers.get('content-range').split('/')[-1]

all_rows = []
offset = 0
while True:
    r = requests.get(f'{u}/rest/v1/questions?select=subject_id,topic_id&limit=1000&offset={offset}', headers=h).json()
    if not r: break
    all_rows.extend(r)
    if len(r) < 1000: break
    offset += 1000

subject_map = defaultdict(Counter)
for row in all_rows:
    subj = row.get('subject_id') or 'unknown'
    top = row.get('topic_id') or 'unknown'
    subject_map[subj][top] += 1

header = f'📊 <b>TRYIT HOURLY REPORT</b>\n\n'
header += f'📚 <b>Total Questions:</b> {total}\n'
header += f'✅ <b>Total Verified (All time):</b> {total}\n'
header += f'🚀 <b>Generated Today (v3):</b> {v3_today}\n'

lines = [header]
current_chunk = header
for subj, topics in sorted(subject_map.items()):
    subj_total = sum(topics.values())
    block = f'\n📂 <b>{subj.replace("_", " ").title()}</b> ({subj_total} Qs)\n'
    for top, count in sorted(topics.items(), key=lambda x: -x[1]):
        block += f'  • <code>{top}</code>: {count} Qs\n'
    
    if len(current_chunk) + len(block) > 4000:
        lines.append(current_chunk)
        current_chunk = block
    else:
        current_chunk += block

if current_chunk:
    lines.append(current_chunk)

for chunk in lines:
    requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': chunk, 'parse_mode': 'HTML'})
print('Telegram Report Sent!')
