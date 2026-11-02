import os, requests
from dotenv import load_dotenv

load_dotenv()

def test_key(provider, key_num, key, url, model, is_gemini=False):
    if not key:
        return f"❌ {provider}_{key_num}: MISSING"
    
    try:
        if is_gemini:
            req_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": "Say OK"}]}]}
            res = requests.post(req_url, json=payload, timeout=10)
        else:
            headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
            payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            
        if res.status_code == 200:
            return f"✅ {provider}_{key_num}: WORKING"
        elif res.status_code == 429:
            return f"⚠️ {provider}_{key_num}: RATE LIMITED / HIGH DEMAND"
        elif res.status_code == 503:
            return f"⚠️ {provider}_{key_num}: SERVER OVERLOADED (503)"
        else:
            return f"❌ {provider}_{key_num}: DEAD (Error {res.status_code})"
    except Exception as e:
        return f"❌ {provider}_{key_num}: CONNECTION ERROR"

print("==================================================")
print("       ULTIMATE CROSS-CHECK REPORT (FINAL)        ")
print("==================================================\n")

# 1. GROQ
print("--- GROQ (Model: openai/gpt-oss-120b) ---")
for i in range(1, 6):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    print(test_key("GROQ", i, key, "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b"))

# 2. NVIDIA
print("\n--- NVIDIA (Model: meta/llama-3.2-90b-vision-instruct) ---")
for i in range(1, 6):
    key = os.getenv(f'NVIDIA_API_KEY_{i}')
    print(test_key("NVIDIA", i, key, "https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.2-90b-vision-instruct"))

# 3. GEMINI (Updated to 3.8-flash)
print("\n--- GEMINI (Model: gemini-3.8-flash) ---")
for i in range(1, 6):
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    print(test_key("GEMINI", i, key, "", "gemini-3.8-flash", is_gemini=True))

# 4. SAMBANOVA (Updated to Gemma)
print("\n--- SAMBANOVA (Model: gemma-4-31B-it) ---")
for i in range(1, 6):
    key = os.getenv(f'SAMBANOVA_API_KEY_{i}')
    print(test_key("SAMBANOVA", i, key, "https://api.sambanova.ai/v1/chat/completions", "gemma-4-31B-it"))

print("\n==================================================")
