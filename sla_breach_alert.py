import os, requests
from datetime import datetime, timezone, timedelta

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

ist = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(ist).isoformat()

r = requests.get(f'{u}/rest/v1/tickets?status=eq.open&sla_deadline=lt.{now}&select=id,issue_type,student_email,sla_deadline,priority',
    headers={**h, 'Prefer': 'count=exact'})

breaches = r.json() if r.ok else []
count = int(r.headers.get('Content-Range','0/0').split('/')[-1])

if count > 0:
    lines = '\n'.join([f"  • {t.get('issue_type','?')} — {t.get('student_email','?')}" for t in breaches[:5]])
    msg = f"🚨 *SLA BREACH ALERT*\n\n{count} ticket(s) have breached SLA:\n{lines}\n{'...' if count > 5 else ''}\n\nAction required immediately → /dashboard/tickets"
    requests.post(f'https://api.telegram.org/bot{tg}/sendMessage',
        json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
    print(f"Alert sent: {count} breaches")
else:
    print("No SLA breaches")