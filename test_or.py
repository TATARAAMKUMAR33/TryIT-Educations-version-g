import requests
# Test with one key directly - paste your actual key here
key = input("Paste one OpenRouter key: ").strip()
r = requests.post("https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
    json={"model":"meta-llama/llama-3.3-70b-instruct:free",
          "messages":[{"role":"user","content":"Say OK"}],
          "max_tokens":10},
    timeout=20)
print("Status:", r.status_code)
print("Response:", r.text[:200])
