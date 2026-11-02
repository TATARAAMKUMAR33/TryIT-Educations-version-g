import os, requests
from dotenv import load_dotenv

load_dotenv()
nvidia_key = os.getenv('NVIDIA_API_KEY_1')

nvidia_models = [
    "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-nano-3-30b-a3b",
    "nvidia/llama3-chatqa-1.5-70b",
    "meta/codellama-70b",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
]

print("--- TESTING REMAINING NVIDIA MODELS ---")
for model in nvidia_models:
    payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
    try:
        res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", 
                            headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"}, 
                            json=payload, timeout=15)
        if res.status_code == 200:
            print(f"  ✅ {model}: WORKING")
        else:
            print(f"  ❌ {model}: DEAD (Error {res.status_code})")
    except Exception:
        print(f"  ❌ {model}: TIMEOUT")
