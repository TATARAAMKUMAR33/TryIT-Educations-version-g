import os, requests, time
from dotenv import load_dotenv
load_dotenv()

print("Testing SambaNova keys...")
for i in range(1,6):
    k = os.getenv(f"SAMBANOVA_API_KEY_{i}")
    if not k:
        print(f"Key {i}: NOT FOUND")
        continue
    
    for model in ["Meta-Llama-3.3-70B-Instruct",
                  "Meta-Llama-3.1-405B-Instruct", 
                  "DeepSeek-R1-Distill-Llama-70B",
                  "Qwen2.5-72B-Instruct",
                  "gemma-4-31B-it"]:
        try:
            start = time.time()
            r = requests.post(
                "https://api.sambanova.ai/v1/chat/completions",
                headers={"Authorization":f"Bearer {k}",
                        "Content-Type":"application/json"},
                json={"model":model,
                      "messages":[{"role":"user","content":"hi"}],
                      "max_tokens":10},
                timeout=20)
            elapsed = time.time()-start
            if r.status_code == 200:
                # Check rate limit headers
                hdrs = dict(r.headers)
                rpm = hdrs.get("x-ratelimit-limit-requests","?")
                rpd = hdrs.get("x-ratelimit-limit-requests-day","?")
                remaining = hdrs.get("x-ratelimit-remaining-requests","?")
                print(f"Key {i} {model}: OK ({elapsed:.1f}s) RPM={rpm} RPD={rpd} remaining={remaining}")
                break
            else:
                print(f"Key {i} {model}: {r.status_code} - {r.text[:60]}")
        except Exception as e:
            print(f"Key {i} {model}: ERR {str(e)[:50]}")
