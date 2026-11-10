"""
Runs daily at 10 AM IST
Finds revenue leakage — paid plans with no payment
Flags to finance team
Cost: ₹0
"""
import os, requests

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}',
     'Content-Type': 'application/json'}

r = requests.get(
    f'{u}/rest/v1/revenue_leakage_alerts?select=alert_type,email,plan',
    headers=h)
alerts = r.json() if r.ok else []

if alerts:
    lines = "\n".join([f"  • {a['alert_type']}: {a['email']}" for a in alerts[:10]])
    msg = f"""💸 *Revenue Leakage Report*

{len(alerts)} issues found:
{lines}
{'...' if len(alerts) > 10 else ''}

Action: Check /dashboard/billing"""
    requests.post(
        f'https://api.telegram.org/bot{tg}/sendMessage',
        json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
    print(f"{len(alerts)} leakage alerts sent")
else:
    print("No leakage detected")