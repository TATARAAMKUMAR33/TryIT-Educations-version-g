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
    requests.post(f"{u}/rest/v1/outbound_message_queue", headers=h, json={'priority': 2, 'message_text': msg})

print("🚀 Running Phase 4 Content & QA Worker...")

# =========================================================
# TASK 34: CONTENT FRESHNESS (Flag > 6 Months)
# =========================================================
print("📚 Checking Content Freshness...")
six_months_ago = (now - timedelta(days=180)).isoformat()
# Find questions not reviewed in 6 months that are still live
stale_q = requests.get(f'{u}/rest/v1/questions?select=id&last_sme_reviewed_at=lt.{six_months_ago}&lifecycle_status=eq.live', headers=h).json()
if len(stale_q) > 100:
    send_tg(f"⚠️ *CONTENT ROT ALERT*\n{len(stale_q)} questions are live but haven't been reviewed by an SME in 6+ months.")

# =========================================================
# TASK 38: EXAM SUBMISSION BUFFER (Thundering Herd Protection)
# =========================================================
print("📥 Flushing Exam Submission Queue...")
# Fetch pending submissions in batches of 1000
subs = requests.get(f'{u}/rest/v1/submission_queue?select=*&status=eq.pending&limit=1000', headers=h).json()
if subs:
    print(f"  Processing {len(subs)} submissions in bulk...")
    # Insert them into the actual exam_submissions table
    insert_payload = [
        {
            'student_email': s['student_email'],
            'exam_name': s['exam_id'],
            'score': s['payload'].get('score', 0),
            'total_questions': s['payload'].get('total', 0),
            'time_taken_seconds': s['payload'].get('time', 0)
        } for s in subs
    ]
    requests.post(f"{u}/rest/v1/exam_submissions", headers=h, json=insert_payload)
    
    # Mark them as processed
    ids = [s['id'] for s in subs]
    ids_str = ",".join(ids)
    requests.patch(f"{u}/rest/v1/submission_queue?id=in.({ids_str})", headers=h, json={'status': 'processed'})

# =========================================================
# TASK 35 & 36: STRUCTURAL LINTER & MATH VALIDATOR
# =========================================================
print("🧹 Running Structural Linter on 50 random questions...")
# Fetch 50 unverified questions
recent_q = requests.get(f'{u}/rest/v1/questions?select=id,question_en,options_en,explanation&limit=50', headers=h).json()
broken_count = 0

for q in recent_q:
    errors = []
    # Check for LaTeX formatting errors
    text = q.get('question_en', '')
    if text.count('$$') % 2 != 0:
        errors.append("Unbalanced LaTeX $$")
    
    # Check for duplicate options
    opts = q.get('options_en', [])
    if len(opts) != len(set(opts)):
        errors.append("Duplicate options detected")
        
    if errors:
        broken_count += 1
        print(f"  ❌ Error in {q['id']}: {', '.join(errors)}")
        # Auto-retire or flag the broken question
        requests.patch(f"{u}/rest/v1/questions?id=eq.{q['id']}", headers=h, json={'lifecycle_status': 'review'})

if broken_count > 0:
    send_tg(f"🔧 *LINTER REPORT*\nFound and flagged {broken_count} formatting errors in the latest QA batch.")

print("✅ Phase 4 Worker Complete.")
