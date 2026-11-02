import os, requests
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("       NVIDIA & GEMINI DEEP DIAGNOSTIC            ")
print("==================================================\n")

# 1. Test NVIDIA Models
nvidia_key = os.getenv('NVIDIA_API_KEY_1')
if not nvidia_key:
    print("❌ No NVIDIA key found.")
else:
    nvidia_models = [
        "meta/llama-3.2-11b-vision-instruct",
        "meta/llama-3.2-90b-vision-instruct",
        "meta/llama2-70b",
        "nvidia/llama-3.1-nemotron-51b-instruct",
        "nvidia/llama-3.1-nemotron-70b-instruct",
        "nvidia/nemotron-3-super-120b-a12b",
        "nvidia/nemotron-4-340b-instruct"
    ]
    
    print("--- TESTING NVIDIA MODELS ---")
    for model in nvidia_models:
        payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
        try:
            res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", 
                                headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"}, 
                                json=payload, timeout=10)
            if res.status_code == 200:
                print(f"  ✅ {model}: WORKING")
            else:
                print(f"  ❌ {model}: DEAD (Error {res.status_code})")
        except Exception:
            print(f"  ❌ {model}: TIMEOUT")

# 2. Test Individual Gemini Keys
print("\n--- TESTING GEMINI KEYS (Model: gemini-3.5-flash) ---")
for i in range(1, 6):
    g_key = os.getenv(f'GEMINI_API_KEY_{i}')
    if not g_key:
        print(f"  ❌ GEMINI_API_KEY_{i}: MISSING")
        continue
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={g_key}"
    payload = {"contents": [{"parts": [{"text": "Say OK"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"  ✅ GEMINI_API_KEY_{i}: WORKING")
        elif res.status_code == 429:
            print(f"  ⚠️ GEMINI_API_KEY_{i}: RATE LIMITED")
        elif res.status_code == 403:
            print(f"  ❌ GEMINI_API_KEY_{i}: DEAD (403 Forbidden - Invalid/Banned Key)")
        else:
            print(f"  ❌ GEMINI_API_KEY_{i}: DEAD (Error {res.status_code})")
    except Exception:
        print(f"  ❌ GEMINI_API_KEY_{i}: TIMEOUT")

print("\n==================================================")
