"""
Runs daily at 6 PM IST
Finds high-churn-risk students
Inserts outbound messages for CRM team
Cost: ₹0
"""
import os, requests
from datetime import datetime, timezone, timedelta

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}',
     'Content-Type': 'application/json'}

r = requests.get(
    f'{u}/rest/v1/churn_risk_score?churn_risk=eq.HIGH&select=email,name,days_inactive,exams_taken,plan',
    headers=h)
at_risk = r.json() if r.ok else []

inserts = []
for student in at_risk[:50]:
    inserts.append({
        'to_number': None,
        'to_email': student['email'],
        'channel': 'email',
        'message_type': 'churn_intervention',
        'content': f"Hi {student.get('name','there')}, we noticed you haven't been active for {student.get('days_inactive',0)} days. Your exam is coming up — come back and practice!",
        'status': 'pending',
        'metadata': {
            'days_inactive': student.get('days_inactive'),
            'exams_taken': student.get('exams_taken'),
            'plan': student.get('plan')
        }
    })

if inserts:
    requests.post(
        f'{u}/rest/v1/outbound_message_queue',
        headers={**h, 'Prefer': 'return=minimal'},
        json=inserts)
    print(f"Queued {len(inserts)} churn interventions")
else:
    print("No high-risk students today")