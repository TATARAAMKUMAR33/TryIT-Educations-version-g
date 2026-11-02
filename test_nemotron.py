import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('NVIDIA_API_KEY_1')
url = "https://integrate.api.nvidia.com/v1/chat/completions"

print(f"Testing key starting with: {key[:10] if key else 'MISSING'}...")

payload = {
    "model": "nvidia/nemotron-3-super-120b-a12b",
    "messages": [{"role": "user", "content": "Say 'System Online' in exactly 2 words."}],
    "max_tokens": 20
}

res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload)

if res.status_code == 200:
    print("✅ SUCCESS! The model is alive and replying:")
    print(res.json()['choices'][0]['message']['content'].strip())
else:
    print(f"❌ FAILED. Status: {res.status_code}")
    print(f"   Error: {res.text[:300]}")
