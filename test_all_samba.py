import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('SAMBANOVA_API_KEY_1')
url = "https://api.sambanova.ai/v1/chat/completions"

models_to_test = [
    "MiniMax-M3.1-Flash",
    "gemma-4-31B-it",
    "gpt-oss-120b",
    "DeepSeek-V3.1",
    "Meta-Llama-3.3-70B-Instruct"
]

print("Testing ALL SambaNova models for availability...\n")

for model in models_to_test:
    print(f"Testing {model}...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'OK'"}],
        "max_tokens": 5
    }
    
    try:
        res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ SUCCESS! {model} is WORKING.")
        else:
            print(f"❌ FAILED {model}: Status {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"❌ ERROR {model}: {e}")
