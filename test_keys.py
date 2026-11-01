import os, requests
from dotenv import load_dotenv

load_dotenv()
print("=== TESTING ALL API KEYS (CORRECTED MODELS) ===\n")

# Test Groq (using the model from your generate_master.py)
print("--- GROQ KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"GROQ_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ GROQ_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ GROQ_{i}: RATE LIMITED (Needs cooldown)")
        else: print(f"❌ GROQ_{i}: ERROR (Status {res.status_code})")
    except: print(f"❌ GROQ_{i}: CONNECTION ERROR")

# Test NVIDIA (using the model from your generate_master.py)
print("\n--- NVIDIA KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"NVIDIA_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "nvidia/nemotron-3-super-120b-a12b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ NVIDIA_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ NVIDIA_{i}: RATE LIMITED")
        else: print(f"❌ NVIDIA_{i}: ERROR (Status {res.status_code})")
    except: print(f"❌ NVIDIA_{i}: CONNECTION ERROR")

# Test Gemini (using the model from your generate_master.py)
print("\n--- GEMINI KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "Hi"}]}]},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ GEMINI_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ GEMINI_{i}: RATE LIMITED")
        else: print(f"❌ GEMINI_{i}: ERROR (Status {res.status_code})")
    except: print(f"❌ GEMINI_{i}: CONNECTION ERROR")
