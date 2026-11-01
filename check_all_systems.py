import os, time, subprocess
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("=" * 70)
print("🩺 FULL SYSTEM DIAGNOSTIC")
print("=" * 70)

# ── 1. CHECK API KEYS ──
print("\n[1/3] 🔑 API KEY HEALTH CHECK:")

# Test NVIDIA
nvidia_key = os.getenv("NVIDIA_API_KEY_1")
if nvidia_key:
    try:
        client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=nvidia_key)
        client.chat.completions.create(model="nvidia/nemotron-3-super-120b-a12b", messages=[{"role": "user", "content": "hi"}], max_tokens=5, timeout=10)
        print("  ✅ NVIDIA: ACTIVE")
    except Exception as e:
        print(f"  ❌ NVIDIA: {str(e)[:60]}")
else:
    print("  ⚪ NVIDIA: NO KEY")

# Test Groq
groq_key = os.getenv("GROQ_API_KEY_1")
if groq_key:
    try:
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
        client.chat.completions.create(model="openai/gpt-oss-120b", messages=[{"role": "user", "content": "hi"}], max_tokens=5, timeout=10)
        print("  ✅ Groq: ACTIVE")
    except Exception as e:
        print(f"  ❌ Groq: {str(e)[:60]}")
else:
    print("  ⚪ Groq: NO KEY")

# Test Gemini
gemini_key = os.getenv("GEMINI_API_KEY_1")
if gemini_key:
    try:
        client = genai.Client(api_key=gemini_key)
        client.models.generate_content(model="gemini-2.5-flash", contents="hi")
        print("  ✅ Gemini: ACTIVE")
    except Exception as e:
        print(f"  ❌ Gemini: {str(e)[:60]}")
else:
    print("  ⚪ Gemini: NO KEY")

# ── 2. CHECK GENERATOR PROCESS ──
print("\n[2/3] ⚙️ QUESTION GENERATOR STATUS:")
result = subprocess.run(["bash", "-c", "ps aux | grep generate_master | grep -v grep"], capture_output=True, text=True)
if result.stdout.strip():
    print("  ✅ generate_master.py is RUNNING")
else:
    print("  ⚠️ generate_master.py is NOT RUNNING (Paused or Crashed)")

# ── 3. CHECK DATABASE GROWTH ──
print("\n[3/3] 📊 QUESTION BANK GROWTH:")
c1 = s.table('questions').select('id', count='exact').execute().count
print(f"  Current Total Questions: {c1}")
print("  Waiting 60 seconds to check growth...")
time.sleep(60)
c2 = s.table('questions').select('id', count='exact').execute().count
delta = c2 - c1
print(f"  60 seconds later: {c2}")
if delta > 0:
    print(f"  ✅ GROWING (+{delta} questions/minute)")
else:
    print("  ⚠️ NOT GROWING (0 questions added in the last minute)")

print("\n" + "=" * 70)
