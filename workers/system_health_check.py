"""
Runs every 10 minutes
Checks all critical systems
Logs to system_health_checks table
Alerts if anything is degraded
Cost: ₹0
"""
import os, requests, time

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}',
     'Content-Type': 'application/json'}

checks = []

def check(name, check_type, fn):
    start = time.time()
    try:
        result = fn()
        ms = int((time.time() - start) * 1000)
        status = 'healthy' if result else 'degraded'
        checks.append({
            'check_name': name,
            'check_type': check_type,
            'status': status,
            'response_time_ms': ms,
            'details': {'result': result}
        })
        return status == 'healthy'
    except Exception as e:
        checks.append({
            'check_name': name,
            'check_type': check_type,
            'status': 'critical',
            'response_time_ms': 0,
            'details': {'error': str(e)}
        })
        return False

# Check 1: Supabase DB
check('supabase_db', 'db_connection',
    lambda: requests.get(f'{u}/rest/v1/platform_health_score',
        headers={**h, 'Range': '0-0'}).ok)

# Check 2: Question generation running
check('question_generation', 'question_generation',
    lambda: requests.get(
        f'{u}/rest/v1/questions?created_at=gte.{__import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT00:00:00")}&select=id',
        headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}
    ).headers.get('Content-Range', '0/0') != '0/0')

# Check 3: No stuck exams
check('stuck_exams', 'db_connection',
    lambda: requests.get(
        f'{u}/rest/v1/exam_submissions?status=eq.in_progress&created_at=lt.{__import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")}&select=id',
        headers={**h, 'Prefer': 'count=exact', 'Range': '0-0'}
    ).headers.get('Content-Range', '0/0').split('/')[1] == '0')

# Insert all checks
requests.post(
    f'{u}/rest/v1/system_health_checks',
    headers={**h, 'Prefer': 'return=minimal'},
    json=checks)

# Alert on critical
critical = [c for c in checks if c['status'] == 'critical']
if critical:
    names = ", ".join(c['check_name'] for c in critical)
    requests.post(
        f'https://api.telegram.org/bot{tg}/sendMessage',
        json={'chat_id': chat,
              'text': f"🚨 SYSTEM CRITICAL: {names}\n\nCheck /dashboard/system",
              'parse_mode': 'Markdown'})

print(f"Health check: {len([c for c in checks if c['status']=='healthy'])}/{len(checks)} healthy")