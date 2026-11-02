import os, requests
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('SAMBANOVA_API_KEY_1')

if not key:
    print("❌ No SambaNova key found.")
else:
    res = requests.get("https://api.sambanova.ai/v1/models", headers={"Authorization": f"Bearer {key}"})
    if res.status_code == 200:
        models = [m['id'] for m in res.json().get('data', [])]
        print(f"✅ Found {len(models)} models on SambaNova account.\n")
        print("=== LIST OF ACTIVE MODELS ===")
        for m in sorted(models):
            print(f" - {m}")
    else:
        print(f"❌ Error: {res.status_code} - {res.text}")
