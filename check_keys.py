"""API Key Health Check v2 — Includes old keys + correct Gemini model"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from google import genai

load_dotenv(dotenv_path=".env")

def mask(k):
    if not k: return "MISSING"
    return k[:8] + "..." + k[-4:] if len(k) > 12 else "INVALID"

def check_openai(name, base_url, key, model):
    if not key or not key.strip():
        return "⚪ MISSING", "no key in .env"
    try:
        client = OpenAI(base_url=base_url, api_key=key)
        client.chat.completions.create(
            model=model, messages=[{"role": "user", "content": "hi"}],
            max_tokens=5, timeout=20,
        )
        return "✅ ACTIVE", f"{model}"
    except Exception as e:
        err = str(e)
        if any(x in err for x in ["401", "403", "invalid", "unauthorized"]):
            return "❌ INVALID", err[:70]
        if "429" in err or "rate" in err.lower():
            return "⚠️ RATE LIMITED", "quota hit but key works"
        if "404" in err:
            return "❌ BAD MODEL", err[:70]
        return "❌ ERROR", err[:70]

def check_gemini(key, model="gemini-2.5-flash"):
    if not key or not key.strip():
        return "⚪ MISSING", "no key in .env"
    try:
        client = genai.Client(api_key=key)
        client.models.generate_content(model=model, contents="hi")
        return "✅ ACTIVE", model
    except Exception as e:
        err = str(e)
        if "API_KEY_INVALID" in err or "401" in err or "403" in err:
            return "❌ INVALID", err[:70]
        if "429" in err or "quota" in err.lower():
            return "⚠️ RATE LIMITED", "quota hit but key works"
        if "404" in err:
            return "❌ BAD MODEL", err[:70]
        return "❌ ERROR", err[:70]

active = failed = missing = 0

print("\n" + "="*72)
print("🔍 NVIDIA (generation) — 5 keys")
print("="*72)
for i in range(1, 6):
    key = os.getenv(f"NVIDIA_API_KEY_{i}")
    status, detail = check_openai(f"NV_{i}", "https://integrate.api.nvidia.com/v1", key, "nvidia/nemotron-3-super-120b-a12b")
    print(f"  Key {i} [{mask(key)}]: {status}  —  {detail}")
    active += 1 if "ACTIVE" in status else 0
    failed += 1 if "ACTIVE" not in status and "MISSING" not in status else 0
    missing += 1 if "MISSING" in status else 0

print("\n" + "="*72)
print("🔍 GROQ (generation) — includes old un-suffixed key")
print("="*72)
groq_keys = [(os.getenv("GROQ_API_KEY"), "OLD")]
groq_keys += [(os.getenv(f"GROQ_API_KEY_{i}"), f"Key {i}") for i in range(1, 6)]
for key, label in groq_keys:
    if key is None: continue
    status, detail = check_openai(f"GR_{label}", "https://api.groq.com/openai/v1", key, "openai/gpt-oss-120b")
    print(f"  {label:<6} [{mask(key)}]: {status}  —  {detail}")
    active += 1 if "ACTIVE" in status else 0
    failed += 1 if "ACTIVE" not in status and "MISSING" not in status else 0
    missing += 1 if "MISSING" in status else 0

print("\n" + "="*72)
print("🔍 GEMINI (verification, model=gemini-2.5-flash) — includes old un-suffixed key")
print("="*72)
gem_keys = [(os.getenv("GEMINI_API_KEY"), "OLD")]
gem_keys += [(os.getenv(f"GEMINI_API_KEY_{i}"), f"Key {i}") for i in range(1, 6)]
for key, label in gem_keys:
    if key is None: continue
    status, detail = check_gemini(key)
    print(f"  {label:<6} [{mask(key)}]: {status}  —  {detail}")
    active += 1 if "ACTIVE" in status else 0
    failed += 1 if "ACTIVE" not in status and "MISSING" not in status else 0
    missing += 1 if "MISSING" in status else 0

print("\n" + "="*72)
print("📊 SUMMARY")
print("="*72)
print(f"  ✅ Active:  {active}")
print(f"  ❌ Failed:  {failed}")
print(f"  ⚪ Missing: {missing}")
print("="*72)
