import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('SAMBANOVA_API_KEY_1')
url = "https://api.sambanova.ai/v1/chat/completions"

payload = {
    "model": "DeepSeek-V3.2",
    "messages": [{"role": "user", "content": "Say 'System Online' in exactly 2 words."}],
    "max_tokens": 20
}

print("Testing SambaNova DeepSeek-V3.2...")
try:
    res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=15)
    if res.status_code == 200:
        print("✅ SUCCESS! DeepSeek-V3.2 is WORKING.")
        print(f"   Reply: {res.json()['choices'][0]['message']['content'].strip()}")
    else:
        print(f"❌ FAILED. Status: {res.status_code}")
        print(f"   Error: {res.text[:200]}")
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")
