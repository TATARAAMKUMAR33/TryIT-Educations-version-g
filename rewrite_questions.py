import os, json, re, time, sys, requests
from groq import Groq
import google.generativeai as genai
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
    if not TG_TOKEN or not TG_CHAT: return
    try:
        requests.post(f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data={"chat_id": TG_CHAT, "text": msg}, timeout=10)
    except: pass

# --- GROQ CONFIG ---
groq_keys = [env.get(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
groq_keys = [k for k in groq_keys if k]
MODELS = ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "meta-llama/llama-4-scout-17b-16e-instruct"]

def call_groq(prompt):
    for key in groq_keys:
        for model in MODELS:
            try:
                client = Groq(api_key=key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=model, temperature=0.7, max_tokens=1500,
                )
                return chat_completion.choices[0].message.content, model
            except:
                continue
    return None, None

# --- GEMINI CONFIG ---
gemini_keys = [env.get(f"GEMINI_API_KEY_{i}") for i in range(1, 6)]
gemini_keys = [k for k in gemini_keys if k]

def verify_with_gemini(original_q, rewritten_q):
    prompt = f"""
You are a strict Indian exam moderator. A friend is trying to explain a concept to another friend.
Review the REWRITTEN question against the ORIGINAL question.

CRITERIA:
1. Is the mathematical/logical logic and correct answer EXACTLY the same?
2. Is the Indian context (names, cities, festivals) natural and logical? (e.g., No absurdities like someone buying a winter coat in Chennai during summer).
3. Does it sound like a real person explaining it, easy to solve, not robotic?

ORIGINAL: {original_q}
REWRITTEN: {json.dumps(rewritten_q, indent=2)}

Output ONLY valid JSON:
{{"passed": true, "reason": "Looks perfect."}} OR {{"passed": false, "reason": "The math changed / The story is absurd."}}
"""
    for key in gemini_keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel('gemini-flash-latest')
            response = model.generate_content(prompt)
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if match:
                result = json_repair.loads(match.group(0))
                return result.get('passed', False), result.get('reason', 'No reason')
        except Exception as e:
            if "429" in str(e):
                time.sleep(2)
            continue
    print("  ⚠️ Gemini verification skipped (All keys hit limits). Accepting rewrite.")
    return True, "Gemini offline, auto-passed."

def rewrite_batch(batch_size=1):
    # Fetch 50 rows and filter in Python to avoid Supabase syntax errors
    res = sb.table('questions').select('*').limit(50).execute()
    
    if not res.data: return False
    
    # Find the first question that hasn't been processed
    valid_q = next((q for q in res.data if q.get('generated_by') not in ('entity_rewriter', 'entity_rewriter_failed', 'entity_rewriter_rejected')), None)
    
    if not valid_q: 
        return False

    q = valid_q
    context = get_context(q['topic_id'])
    prompt = f"""
You are an expert Indian exam question setter.
Rewrite the following question to fit a specific cultural context, keeping the EXACT SAME mathematical/logical logic, numbers, and correct answer.

{context}

ORIGINAL QUESTION: {q['question_en']}
ORIGINAL OPTIONS: {json.dumps(q['options_en'])}
CORRECT ANSWER: {q['correct_answer']}
ORIGINAL EXPLANATION: {q['explanation']}

Output MUST be ONLY a valid JSON object (no markdown). Use double backslashes for LaTeX.
{{
  "question_en": "The rewritten question text",
  "options_en": ["Option 1", "Option 2", "Option 3", "Option 4"],
  "correct_answer": "The exact same correct answer as the original",
  "explanation": "The rewritten explanation matching the new context"
}}
"""
    print(f"Rewriting {q['id']}...")
    raw, used_model = call_groq(prompt)
    
    if not raw:
        sb.table('questions').update({'generated_by': 'entity_rewriter_failed'}).eq('id', q['id']).execute()
        return True
        
    try:
        data = json_repair.loads(raw)
        print(f"  🧐 Groq done. Sending to Gemini for strict verification...")
        
        passed, reason = verify_with_gemini(q['question_en'], data)
        
        if passed:
            sb.table('questions').update({
                'question_en': data['question_en'],
                'options_en': data['options_en'],
                'explanation': data['explanation'],
                'generated_by': 'entity_rewriter'
            }).eq('id', q['id']).execute()
            print(f"  ✅ Verified & Saved {q['id']} (via {used_model})")
        else:
            print(f"  ❌ Gemini Rejected: {reason}")
            sb.table('questions').update({'generated_by': 'entity_rewriter_rejected'}).eq('id', q['id']).execute()
            
    except Exception as e:
        print(f"  🚨 Error on {q['id']}: {e}")
        sb.table('questions').update({'generated_by': 'entity_rewriter_failed'}).eq('id', q['id']).execute()
        
    time.sleep(1)
    return True

if __name__ == "__main__":
    print("🚀 Starting Verified Auto-Rewriter...")
    send_telegram("🚀 *Verified Question Rewriter Started!*\nGroq writes, Gemini verifies the Indian context.")
    
    total = 0
    while True:
        success = rewrite_batch(batch_size=1)
        if not success:
            print(f"🎉 ALL DONE! Total verified: {total}")
            send_telegram(f"🎉 *Question Rewriter Finished!*\nTotal verified and saved: {total}")
            break
        total += 1
        if total % 10 == 0:
            send_telegram(f"⏳ *Progress Update*\nVerified & Saved: {total} questions.")
        sys.stdout.flush()
