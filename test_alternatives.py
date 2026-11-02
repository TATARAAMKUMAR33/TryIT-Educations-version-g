import os, requests
from dotenv import load_dotenv

load_dotenv()

nvidia_key = os.getenv('NVIDIA_API_KEY_1')
gemini_key = os.getenv('GEMINI_API_KEY_1')

print("=== TESTING NVIDIA ALTERNATIVES ===")
nvidia_models = [
    "meta/llama-3.2-11b-vision-instruct",
    "meta/llama2-70b",
    "nvidia/nemotron-4-340b-instruct"
]

for model in nvidia_models:
    payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
    try:
        res = requests.post("https://integrate.api.nvidia.com/v1/chat/completions", headers={"Authorization": f"Bearer {nvidia_key}", "Content-Type": "application/json"}, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ {model}: WORKING")
        else:
            print(f"❌ {model}: {res.status_code}")
    except:
        print(f"❌ {model}: TIMEOUT")

print("\n=== TESTING GEMINI ALTERNATIVES ===")
gemini_models = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash"
]

for model in gemini_models:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
    payload = {"contents": [{"parts": [{"text": "Say OK"}]}]}
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print(f"✅ {model}: WORKING")
        else:
            print(f"❌ {model}: {res.status_code}")
    except:
        print(f"❌ {model}: TIMEOUT")
