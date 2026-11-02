import os, requests, time
from datetime import datetime, timezone
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}
now = datetime.now(timezone.utc)

def send_tg(msg):
    # Instead of sending directly, push to the Queue to respect rate limits
    requests.post(f"{u}/rest/v1/outbound_message_queue", headers=h, json={
        'priority': 1,
        'message_text': msg
    })

print("🚀 Running Phase 2 Infrastructure Worker...")

# =========================================================
# TASK 20: OUTBOUND API QUEUE PROCESSOR (Telegram Rate Limits)
# =========================================================
print("📤 Processing Outbound API Queue...")
messages = requests.get(f'{u}/rest/v1/outbound_message_queue?select=*&status=eq.pending&order=priority.asc', headers=h).json()
for msg in messages[:25]: # Telegram allows 30/sec. We process 25 per run to be safe.
    res = requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': msg['message_text'], 'parse_mode': 'Markdown'})
    if res.status_code == 200:
        requests.patch(f"{u}/rest/v1/outbound_message_queue?id=eq.{msg['id']}", headers=h, json={'status': 'sent'})
        time.sleep(0.1) # 100ms sleep to avoid hitting limits

# =========================================================
# TASK 18: DEPENDENCY HEALTH PINGER
# =========================================================
print("🏥 Running Dependency Pinger...")
deps = {
    'Supabase': f'{u}/rest/v1/',
    'Telegram': f'https://api.telegram.org/bot{tg_token}/getMe',
    'Razorpay': 'https://api.razorpay.com/v1/orders' # Will likely 401, but checks connectivity
}
for name, url in deps.items():
    try:
        res = requests.get(url, headers=h if name == 'Supabase' else {}, timeout=5)
        if res.status_code not in [200, 401]:
            send_tg(f"⚠️ *DEPENDENCY OUTAGE*\n{name} is down. Status: {res.status_code}")
    except:
        send_tg(f"🚨 *CRITICAL OUTAGE*\n{name} is unreachable. Connection failed.")

# =========================================================
# TASK 19: STORAGE CANARY
# =========================================================
print("🐤 Running Storage Canary...")
# Query table sizes using a Postgres RPC (Assuming you have one, or we count rows)
q_count = requests.get(f'{u}/rest/v1/questions?select=id', headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}).headers.get('content-range', '*/0').split('/')[-1]
if int(q_count) > 500000: # Arbitrary threshold for demonstration
    send_tg(f"⚠️ *STORAGE CANARY*\nQuestions table has {q_count} rows. Consider archiving to R2.")

# =========================================================
# TASK 21: MULTI-SIGNAL DUPLICATE ACCOUNT SCANNER
# =========================================================
print("🕵️ Running Multi-Signal Duplicate Scanner...")
# 1. Check for same phone number across multiple accounts
# Note: In a real environment, you'd query a device_hash or phone table. 
# Here we simulate by checking if users share identical state + is_minor flags (just as an example query).
users = requests.get(f'{u}/rest/v1/users?select=email,phone,state_code', headers=h).json()

phone_map = defaultdict(list)
for user in users:
    if user.get('phone'):
        phone_map[user['phone']].append(user['email'])

for phone, emails in phone_map.items():
    if len(emails) > 1:
        print(f"  🚨 Shared Phone {phone} found for: {emails}")
        requests.post(f"{u}/rest/v1/duplicate_account_flags", headers=h, json={
            'primary_email': emails[0],
            'linked_email': emails[1],
            'signal_type': 'phone'
        })

print("✅ Phase 2 Worker Complete.")
