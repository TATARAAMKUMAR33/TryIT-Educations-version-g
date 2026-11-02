import os, requests
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}

print("🤖 Running Automation Engine...")

# 1. Fetch active rules
rules = requests.get(f'{u}/rest/v1/automation_rules?select=*&is_active=eq.true', headers=h).json()

if not rules:
    print("✅ No active rules found.")
    exit()

# 2. Fetch unassigned urgent tickets for the VIP rule
if any(r['trigger_event'] == 'ticket_created' and 'urgent' in r.get('condition_value', '') for r in rules):
    tickets = requests.get(f'{u}/rest/v1/tickets?select=*&priority=eq.urgent&assigned_to=eq.UNASSIGNED_QUEUE', headers=h).json()
    
    for t in tickets:
        print(f"🚨 VIP Alert Triggered for Ticket: {t['id']}")
        # Action: Send Telegram
        msg = f"🚨 *AUTOMATION ALERT* 🚨\n\n*Rule:* Urgent Ticket Escalation\n*Ticket:* {t['issue_type']}\n*Student:* {t['student_email']}"
        requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': msg, 'parse_mode': 'Markdown'})
        
        # Action: Assign to Admin
        requests.patch(f"{u}/rest/v1/tickets?id=eq.{t['id']}", headers=h, json={'assigned_to': 'tatu.ind@hotmail.com'})
        
        # Log execution
        requests.post(f"{u}/rest/v1/automation_logs", headers=h, json={'rule_name': 'Urgent Ticket Escalation', 'action_taken': 'Telegram Alert & Assign to Admin', 'target_id': t['id']})

print("✅ Automation Engine Complete.")
