import os, requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}
now = datetime.now(timezone.utc)

def send_tg(msg):
    requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': msg, 'parse_mode': 'Markdown'})

print("🚨 Checking Incidents (PagerDuty)...")
# 1. Incident Escalation: If triggered > 10 mins ago and not acknowledged
r = requests.get(f'{u}/rest/v1/incidents?select=*&status=eq.triggered', headers=h).json()
for inc in r:
    created_at = datetime.fromisoformat(inc['created_at'].replace('Z', '+00:00'))
    minutes_open = (now - created_at).total_seconds() / 60
    
    if minutes_open > 10:
        print(f"⚠️ Escalating Incident: {inc['title']}")
        send_tg(f"🚨 *INCIDENT ESCALATION* 🚨\n\n*Issue:* {inc['title']}\n*Severity:* {inc['severity']}\n*Status:* Unacknowledged for >10 mins!\n*Action Required by Admin.*")
        
        # Escalate to Admin
        requests.patch(f"{u}/rest/v1/incidents?id=eq.{inc['id']}", headers=h, json={'assigned_to': 'tatu.ind@hotmail.com', 'status': 'acknowledged'})

print("💳 Checking Software Renewals (ServiceNow)...")
# 2. Software Renewal Alerts: If renewal is in 30 days
r_licenses = requests.get(f'{u}/rest/v1/software_licenses?select=*', headers=h).json()
for lic in r_licenses:
    renewal = datetime.fromisoformat(lic['renewal_date'])
    days_left = (renewal - now).days
    
    if days_left <= 30 and days_left >= 0:
        print(f"⚠️ Renewal Due: {lic['tool_name']}")
        send_tg(f"💳 *SOFTWARE RENEWAL ALERT*\n\n*Tool:* {lic['tool_name']}\n*Cost:* ₹{lic['monthly_cost']}/mo\n*Renewal in:* {days_left} days\n*Owner:* {lic['owner_email']}")

print("✅ Enterprise Worker Complete.")
