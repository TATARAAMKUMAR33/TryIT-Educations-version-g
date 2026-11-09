import os, requests
from datetime import datetime, timezone, timedelta

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

ist = timezone(timedelta(hours=5, minutes=30))
today = datetime.now(ist).date().isoformat()

r = requests.get(
    f'{u}/rest/v1/exam_master_calendar?is_active=eq.true&select=exam_name,exam_date,exam_body',
    headers=h)

exams = r.json() if r.ok else []
alerts = []

for e in exams:
    try:
        exam_dt = datetime.fromisoformat(e['exam_date'])
        days = (exam_dt - datetime.fromisoformat(today)).days
        if days in [30, 7, 3, 1, 0]:
            alerts.append((e['exam_name'], e['exam_body'], days))
    except:
        pass

for name, body, days in alerts:
    emoji = '🚨' if days <= 3 else '⚠️' if days <= 7 else '📅'
    urgency = 'CRITICAL' if days <= 3 else 'WARNING' if days <= 7 else 'NOTICE'
    msg = f"""{emoji} *EXAM SURGE {urgency}*

📋 {name} ({body})
⏰ {days} day{'s' if days != 1 else ''} remaining

Action items:
• Enable Battle Mode if traffic spikes
• Ensure CRM team is fully staffed
• Verify all questions are verified in QA
• Pre-load KB articles for this exam

→ Command Center: /dashboard/command-center"""
    requests.post(f'https://api.telegram.org/bot{tg}/sendMessage',
        json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
    print(f"Exam surge alert sent for {name}")