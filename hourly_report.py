import os, requests
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u         = os.getenv("SUPABASE_URL")
k         = os.getenv("SUPABASE_KEY")
tg_token  = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat   = "8486774321"

h     = {"apikey": k, "Authorization": f"Bearer {k}"}
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

def safe_count(url):
    try:
        cr = requests.get(url, headers={**h, "Prefer": "count=exact", "Range": "0-0"}, timeout=10).headers.get("content-range", "0/0")
        return cr.split("/")[-1]
    except Exception:
        return "?"

# 1. COUNTS — track both v3 (old) and v5 (new) and total
total      = safe_count(f"{u}/rest/v1/questions?select=id")
v3_total   = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7")
v5_total   = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7")
v3_today   = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7&created_at=gte.{today}")
v5_today   = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7&created_at=gte.{today}")
today_total = safe_count(f"{u}/rest/v1/questions?select=id&created_at=gte.{today}")

# 2. DIFFICULTY BREAKDOWN — level to label
try:
    diff_rows = requests.get(f"{u}/rest/v1/questions?select=level&created_at=gte.{today}&limit=5000", headers=h, timeout=15).json()
    level_counts = Counter([r.get("level") for r in diff_rows if isinstance(r, dict)])
    easy   = sum(v for l,v in level_counts.items() if l and int(l) <= 3)
    medium = sum(v for l,v in level_counts.items() if l and 4 <= int(l) <= 6)
    hard   = sum(v for l,v in level_counts.items() if l and 7 <= int(l) <= 8)
    expert = sum(v for l,v in level_counts.items() if l and int(l) >= 9)
except Exception:
    easy = medium = hard = expert = 0

# 3. TOPIC BREAKDOWN — paginated
all_rows = []
offset   = 0
while True:
    try:
        r = requests.get(f"{u}/rest/v1/questions?select=subject_id,topic_id&limit=1000&offset={offset}", headers=h, timeout=15).json()
        if not r: break
        all_rows.extend(r)
        if len(r) < 1000: break
        offset += 1000
    except Exception:
        break

subject_map = defaultdict(Counter)
for row in all_rows:
    subj = row.get("subject_id") or "unknown"
    top  = row.get("topic_id")  or "unknown"
    subject_map[subj][top] += 1

# 4. API KEY STATUS — correct models for 2026
def check_key(url, headers, payload):
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=8)
        if res.status_code == 200: return "✅ OK"
        if res.status_code == 429: return "⚠️ Rate limit"
        if res.status_code == 503: return "⚠️ Overloaded"
        return f"❌ {res.status_code}"
    except Exception as e:
        return f"❌ {str(e)[:30]}"

k_status = {"groq": "❌ No key", "nvidia": "❌ No key", "gemini": "❌ No key", "samba": "❌ No key"}

# Groq — correct model
gk = os.getenv("GROQ_API_KEY_1")
if gk:
    k_status["groq"] = check_key(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization": f"Bearer {gk}", "Content-Type": "application/json"},
        {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}
    )

# SambaNova — correct model
sk = os.getenv("SAMBANOVA_API_KEY_1")
if sk:
    k_status["samba"] = check_key(
        "https://api.sambanova.ai/v1/chat/completions",
        {"Authorization": f"Bearer {sk}", "Content-Type": "application/json"},
        {"model": "DeepSeek-V3.2", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}
    )

# NVIDIA — correct model
nk = os.getenv("NVIDIA_API_KEY_1")
if nk:
    k_status["nvidia"] = check_key(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        {"Authorization": f"Bearer {nk}", "Content-Type": "application/json"},
        {"model": "nvidia/nemotron-3-ultra-550b-a55b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}
    )

# Gemini — correct model
gmk = os.getenv("GEMINI_API_KEY_1")
if gmk:
    k_status["gemini"] = check_key(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gmk}",
        {"Content-Type": "application/json"},
        {"contents": [{"parts": [{"text": "Hi"}]}]}
    )

# 5. NEXT RUN TIME
now       = datetime.now(timezone.utc)
next_hour = (now.hour + 1) % 24
next_run  = f"{next_hour:02d}:00 UTC"
ist_hour  = (next_hour + 5) % 24
ist_min   = 30
next_ist  = f"{ist_hour:02d}:{ist_min:02d} IST"

# 6. BUILD MESSAGE
msg  = "📊 <b>TRYIT ENGINE v5 — HOURLY REPORT</b>\n"
msg += f"🕒 {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M UTC')} | Next: {next_run} ({next_ist})\n\n"

msg += "📚 <b>QUESTION COUNTS</b>\n"
msg += f"  Total in DB       : <b>{total}</b>\n"
msg += f"  Generated Today   : <b>{today_total}</b>\n"
msg += f"  v7 engine (new)   : {v5_total} | Today: {v5_today}\n"
msg += f"  v6 engine (prev)   : {v3_total} | Today: {v3_today}\n\n"

msg += "🎯 <b>TODAY BY DIFFICULTY</b>\n"
msg += f"  Easy   (L1-L3)  : {easy}\n"
msg += f"  Medium (L4-L6)  : {medium}\n"
msg += f"  Hard   (L7-L8)  : {hard}\n"
msg += f"  Expert (L9-L10) : {expert}\n\n"

msg += "🔑 <b>API KEY STATUS</b>\n"
msg += f"  Groq      (S1 generate) : {k_status['groq']}\n"
msg += f"  SambaNova (S1+S3)       : {k_status['samba']}\n"
msg += f"  NVIDIA    (S2 explain)  : {k_status['nvidia']}\n"
msg += f"  Gemini    (S4 QA gate)  : {k_status['gemini']}\n\n"

msg += "📌 <b>SUBJECT BREAKDOWN (ALL TIME)</b>\n"

# Split into chunks for Telegram 4096 char limit
def send_tg(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{tg_token}/sendMessage",
            json={"chat_id": tg_chat, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print(f"TG send error: {e}")

current_chunk = msg
for subj, topics in sorted(subject_map.items()):
    subj_total = sum(topics.values())
    block = f"\n📂 <b>{subj.replace('_',' ').title()}</b> ({subj_total} Qs)\n"
    for top, count in sorted(topics.items(), key=lambda x: -x[1])[:10]:
        short = top.replace("competitive_govt_exams_","").replace("ug_pg_entrances_","").replace("nep_school_","")
        block += f"  • {short}: {count}\n"

    if len(current_chunk) + len(block) > 3800:
        send_tg(current_chunk)
        current_chunk = block
    else:
        current_chunk += block

if current_chunk.strip():
    send_tg(current_chunk)

print("✅ Hourly report sent to Telegram!")


