"""Live verification with IST times"""
import os, time, subprocess
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from supabase import create_client

IST = timezone(timedelta(hours=5, minutes=30))
load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

def to_ist_str(utc_str):
    try:
        dt = datetime.fromisoformat(utc_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(IST).strftime('%Y-%m-%d %H:%M:%S IST')
    except:
        return utc_str[:19] if len(utc_str) > 19 else utc_str

print("=" * 70)
print(f"🔍 LIVE CHECK — {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S IST')}")
print("=" * 70)

# CHECK 1: Process
print("\n[1/3] Process check...")
result = subprocess.run(["bash", "-c", "ps aux | grep generate_master | grep -v grep"], capture_output=True, text=True)
if result.stdout.strip():
    line = result.stdout.strip().split("\n")[0]
    print(f"   ✅ Running — PID {line.split()[1]} | CPU {line.split()[2]}%")
else:
    print("   ❌ NOT RUNNING")

# CHECK 2: Count growth
print("\n[2/3] Count snapshot (60s wait)...")
c1 = s.table('questions').select('id', count='exact').execute().count
print(f"   COUNT_NOW = {c1}")
time.sleep(60)
c2 = s.table('questions').select('id', count='exact').execute().count
print(f"   COUNT_AFTER_60s = {c2}")
delta = c2 - c1
print(f"   ➕ Added: {delta}/min | {delta*60}/hour | {delta*60*24}/day")

# CHECK 3: Recent inserts (last 5 min, IST display)
print("\n[3/3] Recent inserts (last 5 min)...")
five_ago = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
recent = s.table('questions').select('topic_id, level, quality_score, exam_tags, created_at').gte('created_at', five_ago).order('created_at', desc=True).limit(5).execute().data
if recent:
    print(f"   ✅ {len(recent)} in last 5 min")
    for q in recent:
        print(f"      {to_ist_str(q['created_at'])} | {q['topic_id'][:35]} L{q['level']} score={q['quality_score']} tags={len(q.get('exam_tags') or [])}")
else:
    print("   ❌ No inserts in last 5 min")

# Verdict
print("\n" + "=" * 70)
if delta > 0 and recent:
    print("✅ HEALTHY — pipeline running, Supabase saving")
elif delta == 0:
    print("⚠️  No growth — check log")
else:
    print("⚠️  Anomaly detected")
print("=" * 70)
