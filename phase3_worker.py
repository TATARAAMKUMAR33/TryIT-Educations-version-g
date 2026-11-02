import os, requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL'); k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}
now = datetime.now(timezone.utc)

def send_tg(msg):
    # Push to Outbound Queue (From Phase 2) to prevent rate limits
    requests.post(f"{u}/rest/v1/outbound_message_queue", headers=h, json={
        'priority': 1,
        'message_text': msg
    })

print("🚀 Running Phase 3 Operations Worker...")

# =========================================================
# TASK 22: EXAM PRE-ALERTS (30 Days Before)
# =========================================================
print("📅 Checking Exam Calendar...")
exams = requests.get(f'{u}/rest/v1/exam_calendar?select=*&pre_alert_sent=eq.false', headers=h).json()
for exam in exams:
    exam_date = datetime.fromisoformat(exam['event_date']).replace(tzinfo=timezone.utc)
    days_left = (exam_date - now).days
    
    if days_left <= 30:
        send_tg(f"🚨 *SURGE PRE-ALERT*\n{exam['exam_name']} {exam['event_type']} is in {days_left} days. Prepare support teams.")
        requests.patch(f"{u}/rest/v1/exam_calendar?id=eq.{exam['id']}", headers=h, json={'pre_alert_sent': True})

# =========================================================
# TASK 23: DEAD LETTER QUEUE (Stale Tickets > 7 Days)
# =========================================================
print("⏳ Checking Dead Letter Queue...")
stale_tickets = requests.get(f'{u}/rest/v1/tickets?select=id,issue_type&status=eq.open', headers=h).json()
for t in stale_tickets:
    updated = datetime.fromisoformat(t['updated_at'].replace('Z', '+00:00'))
    if (now - updated).days > 7:
        send_tg(f"💀 *DEAD LETTER QUEUE*\nTicket {t['issue_type']} has been untouched for 7+ days!")

# =========================================================
# TASK 25: STAFF BURNOUT LIMITER
# =========================================================
print("🔥 Checking Staff Burnout...")
staff = requests.get(f'{u}/rest/v1/staff_roles?select=user_email,backup_email&is_active=eq.true', headers=h).json()
for s in staff:
    email = s['user_email']
    # Count open tickets and tasks
    t_res = requests.get(f'{u}/rest/v1/tickets?select=id&assigned_to=eq.{email}&status=eq.open', headers=h).json()
    task_res = requests.get(f'{u}/rest/v1/tasks?select=id&assigned_to=eq.{email}&status=neq.done', headers=h).json()
    
    workload_score = (len(t_res) * 10) + (len(task_res) * 5)
    if workload_score > 80:
        send_tg(f"🛑 *BURNOUT ALERT*\nStaff {email} has a workload score of {workload_score}. Please reassign tasks.")

# =========================================================
# TASK 28: LEAVE RE-ROUTER
# =========================================================
print("✈️ Checking Staff Leave...")
on_leave = requests.get(f'{u}/rest/v1/staff_roles?select=user_email,backup_email&is_on_leave=eq.true', headers=h).json()
for s in on_leave:
    email = s['user_email']
    backup = s['backup_email']
    if not backup: continue
    
    # Re-route Open Tickets
    requests.patch(f"{u}/rest/v1/tickets?assigned_to=eq.{email}&status=eq.open", headers=h, json={'assigned_to': backup})
    # Re-route Open Tasks
    requests.patch(f"{u}/rest/v1/tasks?assigned_to=eq.{email}&status=neq.done", headers=h, json={'assigned_to': backup})
    
    # Deactivate their flag so we don't run this again until they return
    requests.patch(f"{u}/rest/v1/staff_roles?user_email=eq.{email}", headers=h, json={'is_on_leave': False})
    send_tg(f"🔄 *RE-ROUTER*\n{email} is on leave. Tickets & Tasks moved to backup: {backup}.")

print("✅ Phase 3 Worker Complete.")
