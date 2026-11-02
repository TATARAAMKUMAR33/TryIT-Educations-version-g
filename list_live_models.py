import os, requests
from dotenv import load_dotenv

load_dotenv()

# 1. List NVIDIA Models
nvidia_key = os.getenv('NVIDIA_API_KEY_1')
if nvidia_key:
    print("=== LIVE NVIDIA MODELS ===")
    try:
        res = requests.get("https://integrate.api.nvidia.com/v1/models", headers={"Authorization": f"Bearer {nvidia_key}"})
        if res.status_code == 200:
            models = [m['id'] for m in res.json().get('data', [])]
            for m in models:
                if 'llama' in m.lower() or 'nemotron' in m.lower():
                    print(f" - {m}")
        else:
            print(f"Error: {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"Connection Error: {e}")
else:
    print("No NVIDIA key found.")

# 2. List Gemini Models
gemini_key = os.getenv('GEMINI_API_KEY_1')
if gemini_key:
    print("\n=== LIVE GEMINI MODELS ===")
    try:
        res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}")
        if res.status_code == 200:
            models = [m['name'].replace('models/', '') for m in res.json().get('models', [])]
            for m in models:
                if 'gemini' in m:
                    print(f" - {m}")
        else:
            print(f"Error: {res.status_code} - {res.text[:100]}")
    except Exception as e:
        print(f"Connection Error: {e}")
else:
    print("No Gemini key found.")
