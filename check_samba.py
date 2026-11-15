import os, requests
from dotenv import load_dotenv
load_dotenv()
for i in range(1,6):
    k = os.getenv(f"SAMBANOVA_API_KEY_{i}")
    if not k: continue
    for model in ["Meta-Llama-3.3-70B-Instruct","Meta-Llama-3.1-405B-Instruct","gemma-4-31B-it"]:
        try:
            r = requests.post("https://api.sambanova.ai/v1/chat/completions",
                headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},
                json={"model":model,"messages":[{"role":"user","content":"hi"}],"max_tokens":5},
                timeout=15)
            print(f"SambaNova key{i} {model}: {r.status_code}")
            if r.status_code == 200: break
        except Exception as e:
            print(f"SambaNova key{i} {model}: {str(e)[:40]}")
