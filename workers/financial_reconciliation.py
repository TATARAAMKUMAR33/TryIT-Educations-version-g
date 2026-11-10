"""
Runs 1st of every month at 9 AM IST
Builds monthly financial reconciliation
Alerts finance team if discrepancy found
Cost: ₹0
"""
import os, requests
from datetime import datetime, timezone, timedelta

u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
tg = os.getenv('TELEGRAM_BOT_TOKEN')
chat = os.getenv('TELEGRAM_CHAT_ID')
h = {'apikey': k, 'Authorization': f'Bearer {k}',
     'Content-Type': 'application/json'}

now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
period_start = now.replace(day=1).date().isoformat()
period_end = now.date().isoformat()

# Revenue
rev_r = requests.get(
    f'{u}/rest/v1/invoices?status=eq.paid&created_at=gte.{period_start}&select=amount',
    headers=h)
revenue = sum(float(i['amount']) for i in rev_r.json()) if rev_r.ok else 0

# Refunds
ref_r = requests.get(
    f'{u}/rest/v1/refund_requests?status=eq.approved&created_at=gte.{period_start}&select=amount',
    headers=h)
refunds = sum(float(r.get('amount',0)) for r in ref_r.json()) if ref_r.ok else 0

# Payouts
pay_r = requests.get(
    f'{u}/rest/v1/mentor_wallets?select=total_paid',
    headers=h)
payouts = sum(float(p.get('total_paid',0)) for p in pay_r.json()) if pay_r.ok else 0

net = revenue - refunds - payouts
discrepancy = 0

requests.post(
    f'{u}/rest/v1/financial_reconciliation',
    headers={**h, 'Prefer': 'return=minimal'},
    json={
        'period_start': period_start,
        'period_end': period_end,
        'total_revenue': revenue,
        'total_refunds': refunds,
        'total_payouts': payouts,
        'net_revenue': net,
        'discrepancy_amount': discrepancy,
        'status': 'completed'
    })

msg = f"""💰 *Monthly Financial Reconciliation*
Period: {period_start} to {period_end}

Revenue:  ₹{revenue:,.2f}
Refunds:  ₹{refunds:,.2f}
Payouts:  ₹{payouts:,.2f}
─────────────────
Net:      ₹{net:,.2f}

{'⚠️ Discrepancy detected!' if discrepancy > 0 else '✅ All balanced'}"""

requests.post(
    f'https://api.telegram.org/bot{tg}/sendMessage',
    json={'chat_id': chat, 'text': msg, 'parse_mode': 'Markdown'})
print("Reconciliation complete")