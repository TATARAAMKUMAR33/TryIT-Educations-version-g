import os, requests
from dotenv import load_dotenv

load_dotenv()
print("=== DEEP NVIDIA MODEL TEST ===\n")

# The exact URL from your code
url = "https://integrate.api.nvidia.com/v1/chat/completions"
key = os.getenv("NVIDIA_API_KEY_1")

if not key:
    print("❌ No NVIDIA_API_KEY_1 found.")
    exit()

models_to_test = [
    "meta/llama3-70b-instruct",
    "meta/llama-3.1-8b-instruct",
    "mistralai/mixtral-8x7b-instruct-v0.1",
    "nvidia/nemotron-4-340b-instruct"
]

headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

for model in models_to_test:
    print(f"Testing Model: {model}...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 10,
        "temperature": 0.1
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"  ✅ SUCCESS! This model works.\n")
        elif res.status_code == 404:
            print(f"  ❌ 404 Not Found (Model doesn't exist).\n")
        elif res.status_code == 401:
            print(f"  🔑 401 Unauthorized (Invalid Key).\n")
        elif res.status_code == 429:
            print(f"  ⚠️ 429 Rate Limited.\n")
        else:
            print(f"  ❌ Error {res.status_code}: {res.text[:100]}\n")
    except Exception as e:
        print(f"  ❌ Connection Error: {e}\n")
