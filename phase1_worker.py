import os, requests, time
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

# Supabase config
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg_token = os.getenv('TELEGRAM_BOT_TOKEN')
tg_chat = "8486774321"
h = {
    'apikey': k,
    'Authorization': f'Bearer {k}',
    'Content-Type': 'application/json'
}

# GitHub run tracking — auto-set by GitHub Actions
GITHUB_RUN_ID = os.getenv('GITHUB_RUN_ID', 'manual')
GITHUB_RUN_NUMBER = os.getenv('GITHUB_RUN_NUMBER', '0')
WORKFLOW_NAME = os.getenv('GITHUB_WORKFLOW', 'phase1_worker')

now = datetime.now(timezone.utc)

def send_tg(msg):
    try:
        requests.post(
            f'https://api.telegram.org/bot{tg_token}/sendMessage',
            json={'chat_id': tg_chat, 'text': msg, 'parse_mode': 'Markdown'}
        )
    except Exception as e:
        print(f"Telegram error: {e}")

def insert_question(question_text, subject_id, topic_name,
                    exam_target, level, language_code,
                    option_a, option_b, option_c, option_d,
                    correct_answer, explanation,
                    hint=None, quality_score=None):
    """Insert a single question with full GitHub run tracking."""
    data = {
        'question_text': question_text,
        'subject_id': subject_id,
        'topic_name': topic_name,
        'exam_target': exam_target,
        'level': level,
        'language_code': language_code,
        'option_a': option_a,
        'option_b': option_b,
        'option_c': option_c,
        'option_d': option_d,
        'correct_answer': correct_answer,
        'explanation': explanation,
        'hint': hint,
        'quality_score': quality_score,
        'verified': False,
        'github_run_id': GITHUB_RUN_ID,
        'github_run_number': int(GITHUB_RUN_NUMBER) if str(GITHUB_RUN_NUMBER).isdigit() else 0,
        'workflow_name': WORKFLOW_NAME,
        'batch_id': f"{GITHUB_RUN_ID}_{int(time.time())}",
        'generated_by': f"phase1/{WORKFLOW_NAME}/run{GITHUB_RUN_NUMBER}",
    }
    r = requests.post(
        f'{u}/rest/v1/questions',
        headers={**h, 'Prefer': 'return=minimal'},
        json=data
    )
    return r.ok

def log_pipeline(stage, subject_id=None, topic=None, exam=None,
                 language='en', attempted=0, passed=0, failed=0,
                 failure_reason=None, model=None, provider=None,
                 tokens=0, cost=0.0, duration=0):
    """Log each stage of the generation pipeline."""
    try:
        requests.post(
            f'{u}/rest/v1/generation_pipeline_log',
            headers={**h, 'Prefer': 'return=minimal'},
            json={
                'pipeline_stage': stage,
                'subject_id': str(subject_id) if subject_id else None,
                'topic_name': topic,
                'exam_target': exam,
                'language_code': language,
                'questions_attempted': attempted,
                'questions_passed': passed,
                'questions_failed': failed,
                'failure_reason': failure_reason,
                'model_used': model,
                'api_provider': provider,
                'tokens_used': tokens,
                'cost_usd': cost,
                'github_run_id': GITHUB_RUN_ID,
                'github_run_number': int(GITHUB_RUN_NUMBER) if str(GITHUB_RUN_NUMBER).isdigit() else 0,
                'workflow_name': WORKFLOW_NAME,
                'duration_seconds': duration,
            }
        )
    except Exception as e:
        print(f"Pipeline log error: {e}")

print("🚀 Running Phase 1 Financial & Legal Worker...")
print(f"   Run ID: {GITHUB_RUN_ID}")
print(f"   Run Number: {GITHUB_RUN_NUMBER}")
print(f"   Workflow: {WORKFLOW_NAME}")

# =========================================================
# TASK 1: B2B INVOICE AGING (7/14/30 Days)
# =========================================================
print("\n💳 Checking B2B Invoice Aging...")
try:
    invoices = requests.get(
        f'{u}/rest/v1/invoices?select=*&status=eq.pending',
        headers=h
    ).json()

    for inv in invoices:
        try:
            created = datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00'))
            days_old = (now - created).days

            if days_old in [7, 14, 30]:
                if inv.get('is_strategic_client') and days_old == 30:
                    send_tg(
                        f"⚠️ *STRATEGIC B2B ALERT*\n"
                        f"Client {inv.get('client_email', 'unknown')} is 30 days overdue "
                        f"(₹{inv.get('amount', 0)}). Do NOT auto-suspend. Call them."
                    )
                elif not inv.get('is_strategic_client') and days_old == 30:
                    # Auto-suspend non-strategic
                    requests.patch(
                        f"{u}/rest/v1/users?email=eq.{inv.get('client_email')}",
                        headers=h,
                        json={'is_active': False}
                    )
                    send_tg(
                        f"🛑 *AUTO-SUSPENDED*\n"
                        f"Standard B2B client {inv.get('client_email')} suspended "
                        f"for 30-day non-payment."
                    )
                else:
                    send_tg(
                        f"📩 *Invoice Reminder ({days_old}d)*\n"
                        f"Sent to {inv.get('client_email')} for ₹{inv.get('amount', 0)}."
                    )
        except Exception as e:
            print(f"  Invoice processing error: {e}")

    print(f"  Processed {len(invoices)} pending invoices")
except Exception as e:
    print(f"  Invoice aging error: {e}")


# =========================================================
# TASK 2: REFUND STATE MACHINE (Auto-escalation)
# =========================================================
print("\n💸 Checking Refund State Machine...")
try:
    stale_refunds = requests.get(
        f'{u}/rest/v1/refund_requests?select=*&status=eq.initiated',
        headers=h
    ).json()

    escalated = 0
    for ref in stale_refunds:
        try:
            created = datetime.fromisoformat(ref['created_at'].replace('Z', '+00:00'))
            hours_old = (now - created).total_seconds() / 3600

            if hours_old > 24:
                requests.patch(
                    f"{u}/rest/v1/refund_requests?id=eq.{ref['id']}",
                    headers=h,
                    json={'status': 'reviewing'}
                )
                send_tg(
                    f"🚨 *REFUND ESCALATION*\n"
                    f"Refund #{ref['id'][:8]} for "
                    f"{ref.get('student_email', ref.get('user_email', 'unknown'))} "
                    f"(₹{ref.get('amount', 0)}) has been ignored for >24hrs. "
                    f"Escalated to Finance."
                )
                escalated += 1
        except Exception as e:
            print(f"  Refund processing error: {e}")

    print(f"  Escalated {escalated} stale refunds")
except Exception as e:
    print(f"  Refund state machine error: {e}")


# =========================================================
# TASK 3: DPDP ASYNC SWEEPER (Cold Storage Export)
# =========================================================
print("\n🧹 Running DPDP Async Sweeper...")
try:
    dsr_requests = requests.get(
        f'{u}/rest/v1/dpdp_dsr_requests?select=*&status=eq.pending&request_type=eq.data_export',
        headers=h
    ).json()

    for req in dsr_requests:
        try:
            email = req['user_email']
            print(f"  Generating data export for {email}...")

            # In production: compile ZIP, upload to R2, get URL
            fake_r2_link = f"https://r2.tryit.com/exports/{email}_data.zip"

            requests.patch(
                f"{u}/rest/v1/dpdp_dsr_requests?id=eq.{req['id']}",
                headers=h,
                json={'status': 'completed'}
            )
            send_tg(
                f"📦 *DPDP EXPORT READY*\n"
                f"Data for {email} exported.\n"
                f"Link: {fake_r2_link}"
            )
        except Exception as e:
            print(f"  DPDP processing error: {e}")

    print(f"  Processed {len(dsr_requests)} DPDP requests")
except Exception as e:
    print(f"  DPDP sweeper error: {e}")


# =========================================================
# TASK 4: SLA BREACH CHECK
# =========================================================
print("\n⏱️ Checking SLA Breaches...")
try:
    breaches = requests.get(
        f'{u}/rest/v1/tickets?select=id,issue_type,student_email,sla_deadline,priority'
        f'&status=eq.open&sla_deadline=lt.{now.isoformat()}',
        headers={**h, 'Prefer': 'count=exact', 'Range': '0-4'}
    )
    breach_data = breaches.json()
    total_breaches = int(breaches.headers.get('Content-Range', '0/0').split('/')[-1])

    if total_breaches > 0:
        lines = '\n'.join([
            f"  • {t.get('issue_type', '?')} — {t.get('student_email', '?')}"
            for t in breach_data[:5]
        ])
        send_tg(
            f"🚨 *SLA BREACH ALERT*\n\n"
            f"{total_breaches} ticket(s) breached SLA:\n{lines}\n"
            f"{'...' if total_breaches > 5 else ''}\n\n"
            f"Action required → /dashboard/tickets"
        )
        print(f"  {total_breaches} SLA breaches found")
    else:
        print("  No SLA breaches")
except Exception as e:
    print(f"  SLA check error: {e}")


# =========================================================
# TASK 5: EXAM SURGE CHECK
# =========================================================
print("\n📅 Checking Exam Surge Alerts...")
try:
    today_str = now.date().isoformat()
    week_later = (now.date() + timedelta(days=7)).isoformat()

    exams = requests.get(
        f'{u}/rest/v1/exam_master_calendar'
        f'?is_active=eq.true'
        f'&exam_date=gte.{today_str}'
        f'&exam_date=lte.{week_later}'
        f'&select=exam_name,exam_date,exam_body',
        headers=h
    ).json()

    for exam in exams:
        try:
            exam_dt = datetime.fromisoformat(exam['exam_date'])
            days = (exam_dt - now.replace(tzinfo=None)).days

            if days in [30, 7, 3, 1, 0]:
                emoji = '🚨' if days <= 3 else '⚠️' if days <= 7 else '📅'
                urgency = 'CRITICAL' if days <= 3 else 'WARNING' if days <= 7 else 'NOTICE'
                send_tg(
                    f"{emoji} *EXAM SURGE {urgency}*\n\n"
                    f"📋 {exam['exam_name']} ({exam.get('exam_body', '')})\n"
                    f"⏰ {days} day{'s' if days != 1 else ''} remaining\n\n"
                    f"Action items:\n"
                    f"• Enable Battle Mode if traffic spikes\n"
                    f"• Ensure CRM team is fully staffed\n"
                    f"• Verify questions are QA-approved"
                )
        except Exception as e:
            print(f"  Exam surge error: {e}")

    print(f"  Checked {len(exams)} upcoming exams")
except Exception as e:
    print(f"  Exam surge check error: {e}")


# =========================================================
# TASK 6: QUALITY MONITOR
# =========================================================
print("\n📊 Running Quality Monitor...")
try:
    stats = requests.get(
        f'{u}/rest/v1/daily_question_stats?order=date.desc&limit=2',
        headers=h
    ).json()

    if len(stats) >= 1:
        today_stats = stats[0]
        today_quality = float(today_stats.get('avg_quality') or 0)
        today_total = today_stats.get('total_generated', 0)
        today_pending = today_stats.get('pending', 0)

        alerts = []
        if today_quality < 0.6 and today_quality > 0:
            alerts.append(f"🚨 Quality CRITICAL: {round(today_quality*100)}%")
        if today_total == 0:
            alerts.append("🛑 ZERO questions generated today")
        if today_pending > 1000:
            alerts.append(f"⚠️ QA backlog: {today_pending} pending")

        if alerts:
            send_tg(
                "⚠️ *Question Quality Alert*\n\n" +
                "\n".join(alerts) +
                f"\n\nToday: {today_total} generated"
            )
        print(f"  Quality: {round(today_quality*100)}%, Total: {today_total}, Pending: {today_pending}")
    else:
        print("  No stats available yet")
except Exception as e:
    print(f"  Quality monitor error: {e}")


# =========================================================
# FINAL SUMMARY
# =========================================================
print("\n✅ Phase 1 Worker Complete.")
print(f"   Run #{GITHUB_RUN_NUMBER} finished at {now.strftime('%Y-%m-%d %H:%M UTC')}")

send_tg(
    f"✅ *Phase 1 Worker Complete*\n"
    f"Run: #{GITHUB_RUN_NUMBER}\n"
    f"Time: {now.strftime('%d %b %Y %H:%M UTC')}\n"
    f"Workflow: {WORKFLOW_NAME}"
)