import os, json, re, time, sys, requests
from groq import Groq
from supabase import create_client
from entity_engine import get_context
import json_repair

env = {}
for line in open('.env'):
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    env[k.strip()] = v.strip().strip('"').strip("'")

sb = create_client(env['SUPABASE_URL'], env['SUPABASE_KEY'])

# --- TELEGRAM CONFIG ---
TG_TOKEN = env.get('TELEGRAM_EXAM_BOT_TOKEN') or env.get('TELEGRAM_BOT_TOKEN')
TG_CHAT = env.get('TELEGRAM_EXAM_CHAT_ID') or env.get('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    if not TG_TOKEN or not TG_CHAT:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            data={"chat_id": TG_CHAT, "text": msg},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")

# --- GROQ CONFIG ---
groq_keys = [env.get(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
groq_keys = [k for k in groq_keys if k]

MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct"
]

def call_groq(prompt):
    for key in groq_keys:
        for model in MODELS:
            try:
                client = Groq(api_key=key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model,
                    temperature=0.7,
                    max_tokens=1500,
                )
                return chat_completion.choices[0].message.content, model
            except Exception as e:
                if "429" in str(e):
                    time.sleep(2)
                continue
    return None, None

def rewrite_batch(batch_size=5):
    res = sb.table('questions').select('*').not_.in_('generated_by', ['entity_rewriter', 'entity_rewriter_failed']).limit(batch_size).execute()
    
    if not res.data:
        return False

    for q in res.data:
        context = get_context(q['topic_id'])
        prompt = f"""
You are an expert Indian exam question setter.
Rewrite the following question to fit a specific cultural context, keeping the EXACT SAME mathematical/logical logic, numbers, and correct answer.

{context}

ORIGINAL QUESTION: {q['question_en']}
ORIGINAL OPTIONS: {json.dumps(q['options_en'])}
CORRECT ANSWER: {q['correct_answer']}
ORIGINAL EXPLANATION: {q['explanation']}

Output MUST be ONLY a valid JSON object. Do not use markdown or backticks. If using LaTeX, use double backslashes.
{{
  "question_en": "The rewritten question text",
  "options_en": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correct_answer": "The exact same correct answer as the original",
  "explanation": "The rewritten explanation matching the new context"
}}
"""
        print(f"Rewriting question {q['id']}...")
        raw, used_model = call_groq(prompt)
        
        if not raw:
            print(f"  🚨 All keys/models failed for {q['id']}")
            sb.table('questions').update({'generated_by': 'entity_rewriter_failed'}).eq('id', q['id']).execute()
            continue
            
        try:
            data = json_repair.loads(raw)
            if isinstance(data, dict) and 'question_en' in data:
                sb.table('questions').update({
                    'question_en': data['question_en'],
                    'options_en': data['options_en'],
                    'explanation': data['explanation'],
                    'generated_by': 'entity_rewriter'
                }).eq('id', q['id']).execute()
                print(f"  ✅ Updated {q['id']} (via {used_model})")
            else:
                print(f"  ⚠️ Invalid JSON structure for {q['id']}")
                sb.table('questions').update({'generated_by': 'entity_rewriter_failed'}).eq('id', q['id']).execute()
        except Exception as e:
            print(f"  🚨 Error on {q['id']}: {e}")
            sb.table('questions').update({'generated_by': 'entity_rewriter_failed'}).eq('id', q['id']).execute()
            
        time.sleep(1)

    return True

if __name__ == "__main__":
    print("🚀 Starting continuous batch rewrite...")
    send_telegram("🚀 *Question Auto-Rewriter Started!*\nThe cloud engine is now processing the questions.")
    
    total = 0
    while True:
        success = rewrite_batch(batch_size=5)
        if not success:
            print(f"🎉 ALL DONE! Total questions processed in this run: {total}")
            send_telegram(f"🎉 *Question Auto-Rewriter Finished!*\nTotal questions processed this run: {total}")
            break
        total += 5
        
        # Send a progress update every 50 questions
        if total % 50 == 0:
            send_telegram(f"⏳ *Progress Update*\nRewritten {total} questions so far...")
            
        sys.stdout.flush()
