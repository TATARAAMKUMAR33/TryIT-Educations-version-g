import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(dotenv_path=".env")

providers = [
    ("NVIDIA", "NVIDIA_API_KEY", "https://integrate.api.nvidia.com/v1", "nvidia/nemotron-3-super-120b-a12b"),
    ("SambaNova", "SAMBANOVA_API_KEY", "https://api.sambanova.ai/v1", "Meta-Llama-3.3-70B-Instruct"),
    ("GitHub Models", "GH_MODELS_TOKEN", "https://models.inference.ai.azure.com", "gpt-4o-mini"),
    ("Groq", "GROQ_API_KEY", "https://api.groq.com/openai/v1", "openai/gpt-oss-120b"),
    ("Mistral", "MISTRAL_API_KEY", "https://api.mistral.ai/v1", "mistral-large-latest"),
    ("OpenAI", "OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini"),
]

print("=" * 60)
print("🩺 GENERATION API HEALTH CHECK")
print("=" * 60)

for name, env_prefix, url, model in providers:
    print(f"\n🔍 Testing {name}...")
    # Load up to 5 keys for this provider
    keys = []
    old = os.getenv(env_prefix)
    if old: keys.append(old)
    for i in range(1, 6):
        k = os.getenv(f"{env_prefix}_{i}")
        if k: keys.append(k)
        
    if not keys:
        print(f"  ⚠️ No keys found in .env for {name}")
        continue

    active_count = 0
    for i, key in enumerate(keys):
        try:
            client = OpenAI(base_url=url, api_key=key)
            client.chat.completions.create(
                model=model, 
                messages=[{"role": "user", "content": "Hi"}], 
                max_tokens=5, timeout=10
            )
            print(f"  ✅ Key {i+1} is ACTIVE")
            active_count += 1
        except Exception as e:
            err = str(e)
            if "429" in err: print(f"  ⏳ Key {i+1} is RATE-LIMITED")
            elif "401" in err or "403" in err: print(f"  ❌ Key {i+1} is INVALID (Auth Error)")
            else: print(f"  ❌ Key {i+1} FAILED: {err[:60]}")

    print(f"  ➡️ {name} Total Active: {active_count}/{len(keys)}")

print("\n" + "=" * 60)
