import os, requests
from dotenv import load_dotenv

load_dotenv()

print("=== TESTING ALL API KEYS ON GITHUB CLOUD ===\n")

# Test Groq
print("--- GROQ KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"GROQ_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ GROQ_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ GROQ_{i}: RATE LIMITED")
        else: print(f"❌ GROQ_{i}: DEAD (Status {res.status_code})")
    except: print(f"❌ GROQ_{i}: ERROR")

# Test NVIDIA
print("\n--- NVIDIA KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"NVIDIA_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "meta/llama3-8b-instruct", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ NVIDIA_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ NVIDIA_{i}: RATE LIMITED")
        else: print(f"❌ NVIDIA_{i}: DEAD (Status {res.status_code})")
    except: print(f"❌ NVIDIA_{i}: ERROR")

# Test Gemini
print("\n--- GEMINI KEYS ---")
for i in range(1, 6):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if not key: continue
    try:
        res = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}",
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": "Hi"}]}]},
            timeout=10
        )
        if res.status_code == 200: print(f"✅ GEMINI_{i}: WORKING")
        elif res.status_code == 429: print(f"⚠️ GEMINI_{i}: RATE LIMITED")
        else: print(f"❌ GEMINI_{i}: DEAD (Status {res.status_code})")
    except: print(f"❌ GEMINI_{i}: ERROR")
