import os, requests
from dotenv import load_dotenv

load_dotenv()

def test_provider(name, keys, url, model):
    print(f"\n--- TESTING {name} ---")
    for i, key in enumerate(keys, 1):
        if not key or not key.strip():
            continue
            
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'OK'"}],
            "max_tokens": 5
        }
        
        try:
            res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"✅ {name}_{i}: WORKING")
            else:
                # Print the exact error text from the API
                error_msg = res.text.replace('\n', ' ')[:150]
                print(f"❌ {name}_{i}: ERROR {res.status_code} -> {error_msg}")
        except Exception as e:
            print(f"❌ {name}_{i}: CONNECTION ERROR -> {str(e)[:50]}")

# 1. Test SambaNova (supernova)
samba_keys = [os.getenv(f'SAMBANOVA_API_KEY_{i}') for i in range(1, 6)]
test_provider("SAMBANOVA", samba_keys, "https://api.sambanova.ai/v1/chat/completions", "Meta-Llama-3.3-70B-Instruct")

# 2. Test OpenAI
openai_keys = [os.getenv(f'OPENAI_API_KEY_{i}') for i in range(1, 4)]
test_provider("OPENAI", openai_keys, "https://api.openai.com/v1/chat/completions", "gpt-4o-mini")
