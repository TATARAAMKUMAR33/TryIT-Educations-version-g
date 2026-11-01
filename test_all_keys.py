import os, requests
from dotenv import load_dotenv

load_dotenv()

def test_provider(name, url, headers, payload, key_name):
    for i in range(1, 6):
        key = os.getenv(f"{key_name}_{i}")
        if not key: continue
        
        # Inject the key into headers or URL depending on provider
        req_headers = headers.copy()
        if "Authorization" in req_headers:
            req_headers["Authorization"] = req_headers["Authorization"].replace("YOUR_KEY", key)
        
        req_url = url.replace("YOUR_KEY", key) if "YOUR_KEY" in url else url
        
        try:
            res = requests.post(req_url, headers=req_headers, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"✅ {name}_{i}: WORKING")
            elif res.status_code == 429:
                print(f"⚠️ {name}_{i}: RATE LIMITED (Needs cooldown)")
            elif res.status_code in [401, 403]:
                print(f"❌ {name}_{i}: DEAD (Invalid API Key)")
            elif res.status_code in [404, 410]:
                print(f"❌ {name}_{i}: DEAD (Model not found/retired)")
            else:
                print(f"❌ {name}_{i}: ERROR (Status {res.status_code})")
        except Exception as e:
            print(f"❌ {name}_{i}: CONNECTION ERROR")

print("=== TESTING ALL PROVIDERS ON GITHUB CLOUD ===\n")

# 1. GROQ
print("--- GROQ ---")
test_provider(
    "GROQ", "https://api.groq.com/openai/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "openai/gpt-oss-120b", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "GROQ_API_KEY"
)

# 2. NVIDIA
print("\n--- NVIDIA ---")
test_provider(
    "NVIDIA", "https://integrate.api.nvidia.com/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "nvidia/llama-3.1-nemotron-70b-instruct", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "NVIDIA_API_KEY"
)

# 3. GEMINI
print("\n--- GEMINI ---")
test_provider(
    "GEMINI", "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_KEY",
    {"Content-Type": "application/json"},
    {"contents": [{"parts": [{"text": "Hi"}]}]},
    "GEMINI_API_KEY"
)

# 4. SAMBANOVA
print("\n--- SAMBANOVA ---")
test_provider(
    "SAMBANOVA", "https://api.sambanova.ai/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "Meta-Llama-3.3-70B-Instruct", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "SAMBANOVA_API_KEY"
)

# 5. OPENROUTER
print("\n--- OPENROUTER ---")
test_provider(
    "OPENROUTER", "https://openrouter.ai/api/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "meta-llama/llama-3.3-70b-instruct:free", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "OPENROUTER_API_KEY"
)

# 6. MISTRAL
print("\n--- MISTRAL ---")
test_provider(
    "MISTRAL", "https://api.mistral.ai/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "mistral-large-latest", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "MISTRAL_API_KEY"
)

# 7. OPENAI
print("\n--- OPENAI ---")
test_provider(
    "OPENAI", "https://api.openai.com/v1/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "OPENAI_API_KEY"
)

# 8. GH MODELS
print("\n--- GITHUB MODELS ---")
test_provider(
    "GH_MODELS", "https://models.inference.ai.azure.com/chat/completions",
    {"Authorization": "Bearer YOUR_KEY", "Content-Type": "application/json"},
    {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 1},
    "GH_MODELS_TOKEN"
)
