import os, requests
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("  DEEP DIAGNOSTIC: FINDING GEMINI KEY 2 STATUS    ")
print("==================================================\n")

# 1. Deep dive into Gemini Key 2
print("--- TESTING GEMINI_API_KEY_2 ON ALL MODELS ---")
key2 = os.getenv('GEMINI_API_KEY_2')
if not key2:
    print("  ❌ GEMINI_API_KEY_2: MISSING FROM SECRETS")
else:
    gemini_models = [
        "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", 
        "gemini-3.1-flash-lite", "gemini-2.5-flash", "gemini-2.5-flash-lite", 
        "gemini-flash-latest", "gemini-flash-lite-latest"
    ]
    for model in gemini_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key2}"
        payload = {"contents": [{"parts": [{"text": "Say OK"}]}]}
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"  ✅ Key 2 WORKS with model: {model}")
            elif res.status_code == 403:
                print(f"  ❌ Key 2 FORBIDDEN (403) on model: {model}")
            elif res.status_code == 429:
                print(f"  ⚠️ Key 2 RATE LIMITED on model: {model}")
            else:
                print(f"  ❌ Key 2 ERROR {res.status_code} on model: {model}")
        except Exception as e:
            print(f"  ❌ Key 2 TIMEOUT on model: {model}")

print("\n--- TESTING ALL OTHER KEYS (Standard Models) ---")

# 2. Test other Gemini keys
print("GEMINI (Model: gemini-3.5-flash):")
for i in [1, 3, 4, 5]:
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
    res = requests.post(url, json={"contents": [{"parts": [{"text": "Hi"}]}]}, timeout=10)
    print(f"  Key {i}: Status {res.status_code}")

# 3. Test Groq
print("\nGROQ (Model: openai/gpt-oss-120b):")
for i in range(1, 6):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=10)
    print(f"  Key {i}: Status {res.status_code}")

# 4. Test NVIDIA
print("\nNVIDIA (Model: nvidia/nemotron-3.5-lightning-30b-a3b):")
for i in range(1, 6):
    key = os.getenv(f'NVIDIA_API_KEY_{i}')
    res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "nvidia/nemotron-3.5-lightning-30b-a3b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=15)
    print(f"  Key {i}: Status {res.status_code}")

# 5. Test SambaNova
print("\nSAMBANOVA (Model: gemma-4-31B-it):")
for i in range(1, 6):
    key = os.getenv(f'SAMBANOVA_API_KEY_{i}')
    res = requests.post("https://api.sambanova.ai/v1/chat/completions", headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json={"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}, timeout=10)
    print(f"  Key {i}: Status {res.status_code}")

print("\n==================================================")
