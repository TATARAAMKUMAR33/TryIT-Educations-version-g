import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('NVIDIA_API_KEY_1')
url = "https://integrate.api.nvidia.com/v1/chat/completions"

models_to_test = [
    "nvidia/llama-3.1-nemotron-70b-instruct", # Highly reliable 70B model
    "meta/llama-3.2-90b-vision-instruct",     # 90B model (might require vision payload, but let's test)
    "mistralai/mistral-large-2-instruct"      # Mistral's flagship model
]

for model in models_to_test:
    print(f"\nTesting Model: {model}...")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Say 'Online' in 1 word."}],
        "max_tokens": 10
    }
    
    res = requests.post(url, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, json=payload)
    
    if res.status_code == 200:
        print(f"✅ SUCCESS! {model} is WORKING.")
        print(f"   Reply: {res.json()['choices'][0]['message']['content'].strip()}")
    else:
        print(f"❌ FAILED {model}: Status {res.status_code}")
        print(f"   Error: {res.text[:150]}")
