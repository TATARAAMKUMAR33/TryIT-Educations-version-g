import os, requests, concurrent.futures
from dotenv import load_dotenv

load_dotenv()

def test_key(provider, key_index, key, url, model, headers, payload):
    req_headers = headers.copy()
    if "Authorization" in req_headers:
        req_headers["Authorization"] = req_headers["Authorization"].replace("YOUR_KEY", key)
    
    req_url = url.replace("YOUR_KEY", key) if "YOUR_KEY" in url else url
    payload["model"] = model # Update model for the test
    
    try:
        res = requests.post(req_url, headers=req_headers, json=payload, timeout=10)
        if res.status_code == 200: return f"✅ {provider}_{key_index} | {model}: WORKING"
        elif res.status_code == 429: return f"⚠️ {provider}_{key_index} | {model}: RATE LIMITED"
        elif res.status_code in [401, 403]: return f"❌ {provider}_{key_index} | {model}: DEAD (Invalid Key)"
        elif res.status_code in [404, 410]: return f"❌ {provider}_{key_index} | {model}: DEAD (Model retired)"
        else: return f"❌ {provider}_{key_index} | {model}: ERROR {res.status_code}"
    except Exception as e:
        return f"❌ {provider}_{key_index} | {model}: CONNECTION ERROR"

print("🚀 INITIATING MASTER KEY & MODEL TEST...\n")

tests = []

# 1. GROQ Tests
for i in range(1, 6):
    key = os.getenv(f"GROQ_API_KEY_{i}")
    if key:
        tests.append(("GROQ", i, key, "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))
        tests.append(("GROQ", i, key, "https://api.groq.com/openai/v1/chat/completions", "llama3-8b-8192", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))

# 2. NVIDIA Tests
for i in range(1, 6):
    key = os.getenv(f"NVIDIA_API_KEY_{i}")
    if key:
        tests.append(("NVIDIA", i, key, "https://integrate.api.nvidia.com/v1/chat/completions", "meta/llama-3.1-70b-instruct", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))
        tests.append(("NVIDIA", i, key, "https://integrate.api.nvidia.com/v1/chat/completions", "mistralai/mixtral-8x22b-v0.1", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))

# 3. GEMINI Tests
for i in range(1, 6):
    key = os.getenv(f"GEMINI_API_KEY_{i}")
    if key:
        tests.append(("GEMINI", i, key, "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY", "gemini-2.5-flash", {"Content-Type": "application/json"}, {"contents": [{"parts": [{"text": "Hi"}]}]}))
        tests.append(("GEMINI", i, key, "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=YOUR_KEY", "gemini-1.5-flash", {"Content-Type": "application/json"}, {"contents": [{"parts": [{"text": "Hi"}]}]}))

# 4. SAMBANOVA Tests
for i in range(1, 6):
    key = os.getenv(f"SAMBANOVA_API_KEY_{i}")
    if key:
        tests.append(("SAMBANOVA", i, key, "https://api.sambanova.ai/v1/chat/completions", "Meta-Llama-3.3-70B-Instruct", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))

# 5. OPENAI Tests
for i in range(1, 4):
    key = os.getenv(f"OPENAI_API_KEY_{i}")
    if key:
        tests.append(("OPENAI", i, key, "https://api.openai.com/v1/chat/completions", "gpt-4o-mini", {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"}, {"messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1}))

# Run all tests concurrently for speed
with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
    futures = [executor.submit(test_key, *t) for t in tests]
    for future in concurrent.futures.as_completed(futures):
        print(future.result())

print("\n✅ MASTER TEST COMPLETE.")
