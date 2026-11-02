import os, requests
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("       FINAL DIAGNOSTIC (ALL MODELS & KEYS)       ")
print("==================================================\n")

# 1. GROQ
print("--- GROQ (openai/gpt-oss-120b) ---")
for i in range(1, 6):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    if key:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=10)
        if res.status_code == 200: print(f"  ✅ GROQ_{i}: WORKING")
        elif res.status_code == 429: print(f"  ⚠️ GROQ_{i}: RATE LIMITED")
        else: print(f"  ❌ GROQ_{i}: DEAD ({res.status_code})")

# 2. NVIDIA
print("\n--- NVIDIA (nemotron-3.5-lightning-30b-a3b) ---")
for i in range(1, 6):
    key = os.getenv(f'NVIDIA_API_KEY_{i}')
    if key:
        res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "nvidia/nemotron-3.5-lightning-30b-a3b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=15)
        if res.status_code == 200: print(f"  ✅ NVIDIA_{i}: WORKING")
        elif res.status_code == 429: print(f"  ⚠️ NVIDIA_{i}: RATE LIMITED")
        else: print(f"  ❌ NVIDIA_{i}: DEAD ({res.status_code})")

# 3. GEMINI (Testing all fallbacks for each key)
print("\n--- GEMINI (Testing all fallbacks) ---")
gemini_models = ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-flash-lite-latest"]

for i in range(1, 6):
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if not key:
        print(f"  ❌ GEMINI_{i}: MISSING")
        continue
    
    key_status = "DEAD (All models failed)"
    for model in gemini_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": "Hi"}]}]}, timeout=10)
            if res.status_code == 200:
                key_status = f"✅ WORKING (via {model})"
                break
            elif res.status_code == 429:
                key_status = f"⚠️ RATE LIMITED (via {model})"
                break
        except Exception:
            pass
            
    print(f"  {key_status} [Key {i}]")

# 4. SAMBANOVA
print("\n--- SAMBANOVA (gemma-4-31B-it) ---")
for i in range(1, 6):
    key = os.getenv(f'SAMBANOVA_API_KEY_{i}')
    if key:
        res = requests.post("https://api.sambanova.ai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=10)
        if res.status_code == 200: print(f"  ✅ SAMBANOVA_{i}: WORKING")
        elif res.status_code == 429: print(f"  ⚠️ SAMBANOVA_{i}: RATE LIMITED")
        else: print(f"  ❌ SAMBANOVA_{i}: DEAD ({res.status_code})")
