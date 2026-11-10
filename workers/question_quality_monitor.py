"""
Runs every 6 hours
Checks question quality degradation
Alerts if quality drops below threshold
Cost: ₹0
"""
import os, requests

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}'}

r = requests.get(
    f'{u}/rest/v1/daily_question_stats?order=date.desc&limit=2',
    headers=h)
stats = r.json() if r.ok else []

if len(stats) >= 2:
    today = stats[0]
    yesterday = stats[1]

    today_quality = float(today.get('avg_quality') or 0)
    yesterday_quality = float(yesterday.get('avg_quality') or 0)
    today_total = today.get('total_generated', 0)

    alerts = []

    if today_quality < 0.6:
        alerts.append(f"🚨 Quality CRITICAL: {round(today_quality*100)}% (threshold: 60%)")

    if yesterday_quality > 0 and today_quality < yesterday_quality * 0.8:
        alerts.append(f"📉 Quality dropped {round((yesterday_quality - today_quality)*100)}% vs yesterday")

    if today_total == 0:
        alerts.append("🛑 ZERO questions generated today — worker may be down")

    if today.get('pending', 0) > 1000:
        alerts.append(f"⚠️ QA backlog: {today.get('pending')} questions pending review")

    if alerts:
        msg = "⚠️ *Question Quality Alert*\n\n" + "\n".join(alerts)
        msg += f"\n\nToday: {today_total} generated, {round(today_quality*100)}% quality"
        requests.post(
            f'https://api.telegram.org/bot{tg}/sendMessage',
            json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
        print(f"Alert sent: {len(alerts)} issues")
    else:
        print(f"Quality OK: {round(today_quality*100)}%, {today_total} questions")