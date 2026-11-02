import os, requests
from dotenv import load_dotenv

load_dotenv()

print("=== FINAL GEMINI VERIFICATION ===")
key = os.getenv('GEMINI_API_KEY_1')
model = "gemini-3.8-flash"

if not key:
    print("❌ No Gemini key found.")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"contents": [{"parts": [{"text": "Say 'System Online' in exactly 2 words."}]}]}
    
    try:
        res = requests.post(url, json=payload, timeout=15)
        if res.status_code == 200:
            reply = res.json()['candidates'][0]['content']['parts'][0]['text']
            print(f"✅ SUCCESS! {model} is WORKING.")
            print(f"   Reply: {reply.strip()}")
        else:
            print(f"❌ FAILED. Status: {res.status_code}")
            print(f"   Error: {res.text[:200]}")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
