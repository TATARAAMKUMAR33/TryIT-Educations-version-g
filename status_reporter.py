import os, requests, json
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"

h = {'apikey': k, 'Authorization': f'Bearer {k}'}

# 1. Get DB Stats
r_total = requests.get(f'{u}/rest/v1/questions?select=id', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'})
total = r_total.headers.get('content-range', '*/0').split('/')[-1]

# Get questions created in the last 2 hours (current run)
past_2h = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
r_recent = requests.get(f'{u}/rest/v1/questions?select=id&created_at=gte.{past_2h}', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'})
recent = r_recent.headers.get('content-range', '*/0').split('/')[-1]

# 2. Check API Key Status (Quick Ping)
def check_key(url, headers, payload, is_gemini=False):
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=5)
        if res.status_code == 200: return "✅"
        if res.status_code in [429, 503]: return "⚠️"
        return "❌"
    except:
        return "❌"

key_status = {"groq": "❌", "nvidia": "❌", "gemini": "❌", "samba": "❌"}

# Test Groq
try:
    g_key = os.getenv('GROQ_API_KEY_1')
    if g_key:
        key_status["groq"] = check_key("https://api.groq.com/openai/v1/chat/completions", {"Authorization": f"Bearer {g_key}", "Content-Type": "application/json"}, {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
except: pass

# Test SambaNova
try:
    s_key = os.getenv('SAMBANOVA_API_KEY_1')
    if s_key:
        key_status["samba"] = check_key("https://api.sambanova.ai/v1/chat/completions", {"Authorization": f"Bearer {s_key}", "Content-Type": "application/json"}, {"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
except: pass

# Test NVIDIA
try:
    n_key = os.getenv('NVIDIA_API_KEY_1')
    if n_key:
        key_status["nvidia"] = check_key("https://integrate.api.nvidia.com/v1/chat/completions", {"Authorization": f"Bearer {n_key}", "Content-Type": "application/json"}, {"model": "meta/llama-3.2-90b-vision-instruct", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
except: pass

# Test Gemini
try:
    gem_key = os.getenv('GEMINI_API_KEY_1')
    if gem_key:
        key_status["gemini"] = check_key(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={gem_key}", {"Content-Type": "application/json"}, {"contents": [{"parts": [{"text": "Hi"}]}]})
except: pass

# 3. Calculate Next Run
now = datetime.now(timezone.utc)
next_hour = now.hour - (now.hour % 2) + 2
if next_hour >= 24: next_hour -= 24
next_run = f"{next_hour:02d}:00 UTC"

# 4. Build the Report
msg = f"📊 <b>TRYIT GENERATOR REPORT</b>\n\n"
msg += f"🚀 <b>Generated this run:</b> {recent}\n"
msg += f"📚 <b>Total Questions:</b> {total}\n\n"

msg += f"🔑 <b>LIVE KEY STATUS (Spot Check):</b>\n"
msg += f"  • Groq: {key_status['groq']}\n"
msg += f"  • SambaNova: {key_status['samba']}\n"
msg += f"  • NVIDIA: {key_status['nvidia']}\n"
msg += f"  • Gemini: {key_status['gemini']}\n\n"

msg += f"🕒 <b>Next Scheduled Run:</b> {next_run}\n"

if int(recent) == 0:
    msg += f"\n⚠️ <b>WARNING:</b> 0 questions generated. The APIs may be rate-limited or out of quota. The system will auto-retry on the next run."
else:
    msg += f"\n✅ <b>SUCCESS:</b> The generator is actively producing questions."

url = f'https://api.telegram.org/bot{tg_token}/sendMessage'
payload = {'chat_id': tg_chat, 'text': msg, 'parse_mode': 'HTML'}
requests.post(url, json=payload)
print('✅ Ultimate Report Sent!')
