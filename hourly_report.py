"""
hourly_report.py - TryIT Engine v8 Telegram Report
Sends comprehensive hourly report covering:
- Question counts by engine version
- Difficulty breakdown
- Tier progress
- API key status (correct 2026 models)
- Subject coverage
- Next run time in IST
"""
import os, requests
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()
u        = os.getenv("SUPABASE_URL")
k        = os.getenv("SUPABASE_KEY")
tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
tg_chat  = "8486774321"

h     = {"apikey": k, "Authorization": f"Bearer {k}"}
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

def safe_count(url):
    try:
        cr = requests.get(url, headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=10).headers.get("content-range","0/0")
        return cr.split("/")[-1]
    except:
        return "?"

def send_tg(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{tg_token}/sendMessage",
            json={"chat_id": tg_chat, "text": text, "parse_mode": "HTML"},
            timeout=15
        )
    except Exception as e:
        print(f"TG error: {e}")

# ── 1. QUESTION COUNTS ────────────────────────────────────────────────────────
total         = safe_count(f"{u}/rest/v1/questions?select=id")
today_total   = safe_count(f"{u}/rest/v1/questions?select=id&created_at=gte.{today}")
v8_total      = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v8")
v8_today      = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v8&created_at=gte.{today}")
v7_today      = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v7&created_at=gte.{today}")
v6_today      = safe_count(f"{u}/rest/v1/questions?select=id&generated_by=eq.tryit_v6&created_at=gte.{today}")

# ── 2. DIFFICULTY BREAKDOWN TODAY ─────────────────────────────────────────────
try:
    diff_rows = requests.get(
        f"{u}/rest/v1/questions?select=level&created_at=gte.{today}&limit=5000",
        headers=h, timeout=15).json()
    lc = Counter(int(r.get("level",0)) for r in diff_rows if isinstance(r,dict) and r.get("level"))
    easy   = sum(v for l,v in lc.items() if l<=3)
    medium = sum(v for l,v in lc.items() if 4<=l<=6)
    hard   = sum(v for l,v in lc.items() if 7<=l<=8)
    expert = sum(v for l,v in lc.items() if l>=9)
    level_str = " | ".join([f"L{l}:{v}" for l,v in sorted(lc.items())])
except:
    easy=medium=hard=expert=0
    level_str="?"

# ── 3. TIER PROGRESS ─────────────────────────────────────────────────────────
TIER_SUBJECTS = {
    "T1 School":    ["cbse","icse_board","tn_state","mh_state","ap_ts","karnataka","up_state",
                     "bihar","wb_state","gujarat","punjab","rajasthan","mp_state","kerala",
                     "odisha","assam","nep_school","cbse_maths","cbse_science","cbse_sst",
                     "cbse_physics","cbse_chemistry","cbse_biology"],
    "T2 UG Entry":  ["ug_pg_entrances"],
    "T3 PG/GATE":   ["gate_prep","mba_cat","medical_pg"],
    "T4 PhD":       ["research_academia"],
    "T5 Foreign":   ["study_abroad","international_exams","french","german","spanish",
                     "japanese","mandarin","korean","arabic"],
    "T6 Govt":      ["competitive_govt","ssc_exams","rrb_exams","bank_exams",
                     "defence_exams","upsc_mains"],
    "T7 State":     ["state_exams","tamil_full","telugu_full","kannada_full",
                     "malayalam_full","marathi_full","bengali_full"],
    "T8 Pro":       ["ca_cs_cma","ca_final","finance_cert","law_practice",
                     "usmle","nursing","pharmacy"],
}

try:
    all_q = requests.get(
        f"{u}/rest/v1/questions?select=subject_id&limit=5000",
        headers=h, timeout=20).json()
    subj_counts = Counter(r.get("subject_id","") for r in all_q if isinstance(r,dict))
    tier_counts = {}
    for tier, subjects in TIER_SUBJECTS.items():
        count = sum(v for s,v in subj_counts.items() if any(sub in s for sub in subjects))
        tier_counts[tier] = count
except:
    tier_counts = {}

# ── 4. API KEY STATUS (correct 2026 models) ───────────────────────────────────
def check_key(url, hdr, payload):
    try:
        r = requests.post(url, headers=hdr, json=payload, timeout=10)
        if r.status_code == 200: return "OK"
        if r.status_code == 429: return "RATE LIMITED"
        return f"ERR {r.status_code}"
    except Exception as e:
        return f"ERR {str(e)[:20]}"

k_status = {}

# Groq
gk = os.getenv("GROQ_API_KEY_1","")
if gk:
    k_status["Groq"] = check_key(
        "https://api.groq.com/openai/v1/chat/completions",
        {"Authorization":f"Bearer {gk}","Content-Type":"application/json"},
        {"model":"openai/gpt-oss-120b","messages":[{"role":"user","content":"hi"}],"max_tokens":1}
    )
else:
    k_status["Groq"] = "NO KEY"

# Gemini (REST)
gmk = os.getenv("GEMINI_API_KEY_1","")
if gmk:
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={gmk}",
            json={"contents":[{"parts":[{"text":"hi"}]}]},
            timeout=10
        )
        k_status["Gemini"] = "OK" if r.status_code==200 else f"ERR {r.status_code}"
    except Exception as e:
        k_status["Gemini"] = f"ERR {str(e)[:20]}"
else:
    k_status["Gemini"] = "NO KEY"

# NVIDIA
nk = os.getenv("NVIDIA_API_KEY_1","")
if nk:
    k_status["NVIDIA"] = check_key(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        {"Authorization":f"Bearer {nk}","Content-Type":"application/json"},
        {"model":"nvidia/nemotron-3-ultra-550b-a55b","messages":[{"role":"user","content":"hi"}],"max_tokens":1}
    )
else:
    k_status["NVIDIA"] = "NO KEY"

# SambaNova (removed - show as REMOVED)
k_status["SambaNova"] = "REMOVED (410 error)"

# ── 5. TOPIC COVERAGE ─────────────────────────────────────────────────────────
try:
    topics_total = requests.get(
        f"{u}/rest/v1/topics?select=id",
        headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=10
    ).headers.get("content-range","?").split("/")[-1]

    # Topics with at least 1 question
    topics_with_q = requests.get(
        f"{u}/rest/v1/questions?select=topic_id&limit=5000",
        headers=h, timeout=15).json()
    unique_topics = len(set(r.get("topic_id") for r in topics_with_q if isinstance(r,dict)))
except:
    topics_total = "?"
    unique_topics = "?"

# ── 6. SUBJECT BREAKDOWN ─────────────────────────────────────────────────────
try:
    all_rows = []
    offset = 0
    while True:
        r = requests.get(
            f"{u}/rest/v1/questions?select=subject_id,topic_id&limit=1000&offset={offset}",
            headers=h, timeout=15).json()
        if not r: break
        all_rows.extend(r)
        if len(r) < 1000: break
        offset += 1000

    subject_map = defaultdict(Counter)
    for row in all_rows:
        subj = (row.get("subject_id") or "unknown").replace("_"," ").title()
        top  = row.get("topic_id") or "unknown"
        subject_map[subj][top] += 1
except:
    subject_map = {}

# ── 7. NEXT RUN TIME ─────────────────────────────────────────────────────────
now = datetime.now(timezone.utc)
# Runs every 3 hours
next_hour = ((now.hour // 3) + 1) * 3
if next_hour >= 24: next_hour = 0
next_utc  = f"{next_hour:02d}:00 UTC"
ist_hour  = (next_hour + 5) % 24
ist_min   = 30
next_ist  = f"{ist_hour:02d}:{ist_min:02d} IST"

# ── 8. BUILD MESSAGE ─────────────────────────────────────────────────────────
def sts(s):
    return "OK" if s=="OK" else s

msg  = f"<b>TRYIT ENGINE v8 — HOURLY REPORT</b>\n"
msg += f"{now.strftime('%d %b %Y %H:%M UTC')} | Next: {next_utc} ({next_ist})\n\n"

msg += "<b>QUESTION COUNTS</b>\n"
msg += f"  Total in DB       : <b>{total}</b>\n"
msg += f"  Generated Today   : <b>{today_total}</b>\n"
msg += f"  v8 (current)      : {v8_total} | Today: {v8_today}\n"
msg += f"  v7 (previous)     : Today: {v7_today}\n"
msg += f"  v6 (old)          : Today: {v6_today}\n\n"

msg += "<b>TODAY BY DIFFICULTY</b>\n"
msg += f"  Easy   (L1-L3)  : {easy}\n"
msg += f"  Medium (L4-L6)  : {medium}\n"
msg += f"  Hard   (L7-L8)  : {hard}\n"
msg += f"  Expert (L9-L10) : {expert}\n"
msg += f"  Levels: {level_str}\n\n"

msg += "<b>TOPIC COVERAGE</b>\n"
msg += f"  Total topics     : {topics_total}\n"
msg += f"  Topics with Q's  : {unique_topics}\n\n"

msg += "<b>TIER PROGRESS (All Time)</b>\n"
for tier, count in tier_counts.items():
    bar = "=" * min(20, count//100)
    msg += f"  {tier}: {count} {bar}\n"
msg += "\n"

msg += "<b>API STATUS</b>\n"
msg += f"  Groq   (GEN primary)  : {sts(k_status.get('Groq','?'))}\n"
msg += f"  Gemini (GEN+QA)       : {sts(k_status.get('Gemini','?'))}\n"
msg += f"  NVIDIA (L8-10 upgrade): {sts(k_status.get('NVIDIA','?'))}\n"
msg += f"  SambaNova             : {k_status.get('SambaNova','?')}\n\n"

# Split subject breakdown into chunks
send_tg(msg)

# Subject breakdown as separate message
subj_msg = "<b>SUBJECT BREAKDOWN (ALL TIME)</b>\n"
current_chunk = subj_msg

for subj, topics in sorted(subject_map.items()):
    subj_total = sum(topics.values())
    if subj_total < 2: continue  # Skip tiny subjects
    block = f"\n<b>{subj}</b> ({subj_total} Qs)\n"
    # Show top 5 topics per subject
    for top, count in sorted(topics.items(), key=lambda x: -x[1])[:5]:
        short = top.replace("competitive_govt_exams_","").replace("ug_pg_entrances_","") \
                   .replace("nep_school_foundation_","").replace("maths_","") \
                   .replace("english_","").replace("gk_","").replace("reasoning_","")
        block += f"  {short}: {count}\n"

    if len(current_chunk) + len(block) > 3800:
        send_tg(current_chunk)
        current_chunk = block
    else:
        current_chunk += block

if current_chunk.strip():
    send_tg(current_chunk)

print("Hourly report sent to Telegram!")