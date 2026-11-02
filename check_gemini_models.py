import os, requests
from dotenv import load_dotenv

load_dotenv()

print("=== FETCHING LIVE GEMINI MODELS PER KEY ===\n")

for i in range(1, 6):
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if not key:
        print(f"❌ GEMINI_API_KEY_{i}: MISSING from secrets")
        continue
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            models = [m['name'].replace('models/', '') for m in res.json().get('models', [])]
            # Filter only Gemini models for readability
            gemini_models = [m for m in models if 'gemini' in m]
            print(f"✅ GEMINI_API_KEY_{i}: WORKING")
            print(f"   Available Models: {', '.join(gemini_models[:5])}...\n")
        else:
            print(f"❌ GEMINI_API_KEY_{i}: DEAD/ERROR (Status: {res.status_code})")
            print(f"   Reason: {res.text[:150]}\n")
    except Exception as e:
        print(f"❌ GEMINI_API_KEY_{i}: CONNECTION ERROR\n")
