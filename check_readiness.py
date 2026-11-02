import os, requests
from dotenv import load_dotenv

load_dotenv()

print("==================================================")
print("       READ-ONLY KEY STATUS CHECK                 ")
print("==================================================\n")

def check_status(url, headers, payload, is_gemini=False):
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200: return "✅ READY"
        elif res.status_code == 429: return "⚠️ COOLDOWN (Will reset soon)"
        elif res.status_code == 403: return "❌ BANNED/INVALID (403)"
        else: return f"❌ ERROR ({res.status_code})"
    except Exception:
        return "❌ TIMEOUT"

# 1. GROQ
print("--- GROQ (openai/gpt-oss-120b) ---")
for i in range(1, 6):
    key = os.getenv(f'GROQ_API_KEY_{i}')
    if key:
        status = check_status("https://api.groq.com/openai/v1/chat/completions", 
                              {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, 
                              {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
        print(f"  Key {i}: {status}")

# 2. NVIDIA
print("\n--- NVIDIA (nvidia/nemotron-3.5-lightning-30b-a3b) ---")
for i in range(1, 6):
    key = os.getenv(f'NVIDIA_API_KEY_{i}')
    if key:
        status = check_status("https://integrate.api.nvidia.com/v1/chat/completions", 
                              {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, 
                              {"model": "nvidia/nemotron-3.5-lightning-30b-a3b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
        print(f"  Key {i}: {status}")

# 3. GEMINI
print("\n--- GEMINI (gemini-3.5-flash) ---")
for i in range(1, 6):
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent?key={key}"
        status = check_status(url, {}, {"contents": [{"parts": [{"text": "Hi"}]}]}, is_gemini=True)
        print(f"  Key {i}: {status}")

# 4. SAMBANOVA
print("\n--- SAMBANOVA (gemma-4-31B-it) ---")
for i in range(1, 6):
    key = os.getenv(f'SAMBANOVA_API_KEY_{i}')
    if key:
        status = check_status("https://api.sambanova.ai/v1/chat/completions", 
                              {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, 
                              {"model": "gemma-4-31B-it", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1})
        print(f"  Key {i}: {status}")

print("\n==================================================")
