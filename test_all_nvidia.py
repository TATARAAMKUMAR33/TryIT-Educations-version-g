import os, requests
from dotenv import load_dotenv

load_dotenv()
url = "https://integrate.api.nvidia.com/v1/chat/completions"
model = "meta/llama-3.2-90b-vision-instruct"

print(f"Testing all NVIDIA keys against model: {model}\n")

for i in range(1, 6):
    key = os.getenv(f'NVIDIA_API_KEY_{i}')
    if not key:
        print(f"❌ NVIDIA_API_KEY_{i}: NOT FOUND in .env")
        continue
        
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK'"}],
        "max_tokens": 5
    }
    
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ NVIDIA_API_KEY_{i}: WORKING")
        elif res.status_code == 429:
            print(f"⚠️ NVIDIA_API_KEY_{i}: RATE LIMITED")
        elif res.status_code in [401, 403]:
            print(f"❌ NVIDIA_API_KEY_{i}: DEAD (Invalid Key)")
        else:
            print(f"❌ NVIDIA_API_KEY_{i}: ERROR {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"❌ NVIDIA_API_KEY_{i}: CONNECTION ERROR")
