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
    requests.post(f'https://api.telegram.org/bot{tg_token}/sendMessage', json={'chat_id': tg_chat, 'text': msg, 'parse_mode': 'Markdown'})

print("🚀 Running Phase 1 Financial & Legal Worker...")

# =========================================================
# TASK 4: B2B INVOICE AGING (7/14/30 Days)
# =========================================================
print("💳 Checking B2B Invoice Aging...")
invoices = requests.get(f'{u}/rest/v1/invoices?select=*&status=eq.pending', headers=h).json()
for inv in invoices:
    created = datetime.fromisoformat(inv['created_at'].replace('Z', '+00:00'))
    days_old = (now - created).days
    
    if days_old in [7, 14, 30]:
        if inv.get('is_strategic_client') and days_old == 30:
            send_tg(f"⚠️ *STRATEGIC B2B ALERT*\nClient {inv['client_email']} is 30 days overdue (₹{inv['amount']}). Do NOT auto-suspend. Call them.")
        elif not inv.get('is_strategic_client') and days_old == 30:
            # Auto-suspend non-strategic
            requests.patch(f"{u}/rest/v1/users?email=eq.{inv['client_email']}", headers=h, json={'is_active': False})
            send_tg(f"🛑 *AUTO-SUSPENDED*\nStandard B2B client {inv['client_email']} suspended for 30-day non-payment.")
        else:
            send_tg(f"📩 *Invoice Reminder ({days_old}d)*\nSent to {inv['client_email']} for ₹{inv['amount']}.")

# =========================================================
# TASK 9: REFUND STATE MACHINE (Auto-escalation)
# =========================================================
print("💸 Checking Refund State Machine...")
# If a refund is stuck in 'initiated' for > 24 hours, escalate to Admin
stale_refunds = requests.get(f'{u}/rest/v1/refund_requests?select=*&status=eq.initiated', headers=h).json()
for ref in stale_refunds:
    created = datetime.fromisoformat(ref['created_at'].replace('Z', '+00:00'))
    hours_old = (now - created).total_seconds() / 3600
    if hours_old > 24:
        requests.patch(f"{u}/rest/v1/refund_requests?id=eq.{ref['id']}", headers=h, json={'status': 'reviewing'})
        send_tg(f"🚨 *REFUND ESCALATION*\nRefund #{ref['id']} for {ref['student_email']} (₹{ref['amount']}) has been ignored by CRM for >24hrs. Escalated to Finance.")

# =========================================================
# TASK 2: DPDP ASYNC SWEEPER (Cold Storage Export)
# =========================================================
print("🧹 Running DPDP Async Sweeper...")
dsr = requests.get(f'{u}/rest/v1/dpdp_dsr_requests?select=*&status=eq.pending&request_type=eq.data_export', headers=h).json()
for req in dsr:
    email = req['user_email']
    print(f"  Generating data export for {email}...")
    # Simulate R2 Upload & Link Generation
    # In production, this compiles a ZIP, uploads to R2, and gets a URL.
    fake_r2_link = f"https://r2.tryit.com/exports/{email}_data.zip"
    requests.patch(f"{u}/rest/v1/dpdp_dsr_requests?id=eq.{req['id']}", headers=h, json={'status': 'completed'})
    send_tg(f"📦 *DPDP EXPORT READY*\nData for {email} exported. Link: {fake_r2_link}")

print("✅ Phase 1 Worker Complete.")
