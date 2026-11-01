import os, requests
from dotenv import load_dotenv

load_dotenv()

print("=== FETCHING LIVE AVAILABLE MODELS ===\n")

# 1. NVIDIA
nvidia_key = os.getenv('NVIDIA_API_KEY_1')
if nvidia_key:
    try:
        res = requests.get("https://integrate.api.nvidia.com/v1/models", headers={"Authorization": f"Bearer {nvidia_key}"})
        if res.status_code == 200:
            models = [m['id'] for m in res.json().get('data', [])]
            print(f"✅ NVIDIA ({len(models)} models found). Here are the best ones for reasoning:")
            for m in models:
                if 'llama' in m.lower() or 'mistral' in m.lower() or 'nemotron' in m.lower():
                    print(f"   - {m}")
        else:
            print(f"❌ NVIDIA Error: {res.status_code}")
    except Exception as e:
        print(f"❌ NVIDIA Connection Error: {e}")

# 2. Gemini
gemini_key = os.getenv('GEMINI_API_KEY_1')
if gemini_key:
    try:
        res = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}")
        if res.status_code == 200:
            models = [m['name'].replace('models/', '') for m in res.json().get('models', [])]
            print(f"\n✅ GEMINI ({len(models)} models found). Here are the valid ones:")
            for m in models:
                if 'gemini' in m:
                    print(f"   - {m}")
        else:
            print(f"❌ GEMINI Error: {res.status_code}")
    except Exception as e:
        print(f"❌ GEMINI Connection Error: {e}")

# 3. Groq
groq_key = os.getenv('GROQ_API_KEY_1')
if groq_key:
    try:
        res = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {groq_key}"})
        if res.status_code == 200:
            models = [m['id'] for m in res.json().get('data', [])]
            print(f"\n✅ GROQ ({len(models)} models found). Here are the valid ones:")
            for m in models:
                if 'llama' in m.lower() or 'mixtral' in m.lower() or 'gpt' in m.lower():
                    print(f"   - {m}")
        else:
            print(f"❌ GROQ Error: {res.status_code}")
    except Exception as e:
        print(f"❌ GROQ Connection Error: {e}")

# 4. SambaNova
samba_key = os.getenv('SAMBANOVA_API_KEY_1')
if samba_key:
    try:
        res = requests.get("https://api.sambanova.ai/v1/models", headers={"Authorization": f"Bearer {samba_key}"})
        if res.status_code == 200:
            models = [m['id'] for m in res.json().get('data', [])]
            print(f"\n✅ SAMBANOVA ({len(models)} models found). Here are the valid ones:")
            for m in models:
                print(f"   - {m}")
        else:
            print(f"❌ SAMBANOVA Error: {res.status_code}")
    except Exception as e:
        print(f"❌ SAMBANOVA Connection Error: {e}")

print("\n✅ MODEL CHECK COMPLETE.")
