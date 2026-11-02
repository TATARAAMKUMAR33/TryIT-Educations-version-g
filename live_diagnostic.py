import os, requests
from dotenv import load_dotenv

load_dotenv()

def test_model(provider, url, model, headers, payload, is_gemini=False):
    print(f"\n--- Testing {provider} | Model: {model} ---")
    for i in range(1, 6):
        key_name = f"{provider.upper()}_API_KEY_{i}"
        key = os.getenv(key_name)
        if not key: 
            print(f"  ❌ {key_name}: MISSING")
            continue
        
        try:
            if is_gemini:
                req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
                res = requests.post(req_url, json=payload, timeout=15)
            else:
                req_headers = headers.copy()
                req_headers["Authorization"] = f"Bearer {key}"
                res = requests.post(url, headers=req_headers, json=payload, timeout=15)
                
            if res.status_code == 200:
                print(f"  ✅ {key_name}: WORKING")
            elif res.status_code == 429:
                print(f"  ⚠️ {key_name}: RATE LIMITED")
            else:
                print(f"  ❌ {key_name}: DEAD (Error {res.status_code})")
        except Exception as e:
            print(f"  ❌ {key_name}: TIMEOUT/CONNECTION ERROR")

print("==================================================")
print("       LIVE MODEL DIAGNOSTIC (NO CHANGES)         ")
print("==================================================")

# 1. Groq
test_model(
    "groq", 
    "https://api.groq.com/openai/v1/chat/completions", 
    "openai/gpt-oss-120b", 
    {"Content-Type": "application/json"}, 
    {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
)

# 2. NVIDIA
test_model(
    "nvidia", 
    "https://integrate.api.nvidia.com/v1/chat/completions", 
    "meta/llama-3.1-8b-instruct", 
    {"Content-Type": "application/json"}, 
    {"model": "meta/llama-3.1-8b-instruct", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
)

# 3. Gemini
test_model(
    "gemini", 
    "", 
    "gemini-3.5-flash", 
    {}, 
    {"contents": [{"parts": [{"text": "Say OK"}]}]}, 
    is_gemini=True
)

# 4. SambaNova
test_model(
    "sambanova", 
    "https://api.sambanova.ai/v1/chat/completions", 
    "gemma-4-31B-it", 
    {"Content-Type": "application/json"}, 
    {"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
)

print("\n==================================================")
