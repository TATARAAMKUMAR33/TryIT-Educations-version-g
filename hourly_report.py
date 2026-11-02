import os, requests
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"

h = {'apikey': k, 'Authorization': f'Bearer {k}'}
today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

# 1. Fetch Stats
total = requests.get(f'{u}/rest/v1/questions?select=id', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}).headers.get('content-range').split('/')[-1]
v3_total = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}).headers.get('content-range').split('/')[-1]
v3_today = requests.get(f'{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v3&created_at=gte.{today}', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}).headers.get('content-range').split('/')[-1]

# 2. Fetch Topics (Paginated)
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

# 3. Check API Keys (Spot Check)
def check_key(url, headers, payload):
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200: return "✅"
        if res.status_code in [429, 503]: return "⚠️"
        return "❌"
    except: return "❌"

k_status = {"groq": "❌", "nvidia": "❌", "gemini": "❌", "samba": "❌"}

if os.getenv('GROQ_API_KEY_1'): k_status["groq"] = check_key("https://api.groq.com/openai/v1/chat/completions", {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY_1')}", "Content-Type": "application/json"}, {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
if os.getenv('SAMBANOVA_API_KEY_1'): k_status["samba"] = check_key("https://api.sambanova.ai/v1/chat/completions", {"Authorization": f"Bearer {os.getenv('SAMBANOVA_API_KEY_1')}", "Content-Type": "application/json"}, {"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
if os.getenv('NVIDIA_API_KEY_1'): k_status["nvidia"] = check_key("https://integrate.api.nvidia.com/v1/chat/completions", {"Authorization": f"Bearer {os.getenv('NVIDIA_API_KEY_1')}", "Content-Type": "application/json"}, {"model": "meta/llama-3.2-90b-vision-instruct", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
if os.getenv('GEMINI_API_KEY_1'): k_status["gemini"] = check_key(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={os.getenv('GEMINI_API_KEY_1')}", {"Content-Type": "application/json"}, {"contents": [{"parts": [{"text": "Hi"}]}]})

# 4. Next Run
now = datetime.now(timezone.utc)
next_hour = now.hour - (now.hour % 2) + 2
if next_hour >= 24: next_hour -= 24
next_run = f"{next_hour:02d}:00 UTC"

# 5. Build Message
header = f"📊 <b>TRYIT MASTER REPORT</b>\n\n"
header += f"📚 <b>Total Questions:</b> {total}\n"
header += f"✅ <b>Total Verified:</b> {v3_total}\n"
header += f"🚀 <b>Generated Today:</b> {v3_today}\n\n"
header += f"🔑 <b>API STATUS:</b>\n"
header += f"  • Groq: {k_status['groq']}\n"
header += f"  • SambaNova: {k_status['samba']}\n"
header += f"  • NVIDIA: {k_status['nvidia']}\n"
header += f"  • Gemini: {k_status['gemini']}\n\n"
header += f"🕒 <b>Next Run:</b> {next_run}\n\n"
header += f"📌 <b>TOPIC BREAKDOWN:</b>\n"

lines = [header]
current_chunk = header

for subj, topics in sorted(subject_map.items()):
    subj_total = sum(topics.values())
    block = f"\n📂 <b>{subj.replace('_', ' ').title()}</b> ({subj_total} Qs)\n"
    for top, count in sorted(topics.items(), key=lambda x: -x[1]):
        block += f"  • <code>{top}</code>: {count} Qs\n"
    
    if len(current_chunk) + len(block) > 4000:
        lines.append(current_chunk)
        current_chunk = block
    else:
        current_chunk += block

if current_chunk:
    lines.append(current_chunk)

# 6. Send (Split into chunks if necessary)
for chunk in lines:
    requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': chunk, 'parse_mode': 'HTML'})

print('✅ Master Report Sent!')
