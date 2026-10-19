import os, json, re, time, sys
from groq import Groq
from supabase import create_client
from entity_engine import get_context

env = {}
for line in open('.env'):
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    env[k.strip()] = v.strip().strip('"').strip("'")

sb = create_client(env['SUPABASE_URL'], env['SUPABASE_KEY'])

groq_keys = [env.get(f"GROQ_API_KEY_{i}") for i in range(1, 6)]
groq_keys = [k for k in groq_keys if k]

# Put the working model first to save time!
MODELS = [
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "qwen/qwen3-32b"
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
                # If rate limited, wait 2 seconds before trying next
                if "429" in str(e):
                    time.sleep(2)
                continue
    return None, None

def rewrite_batch(batch_size=5):
    # THE FIX: Query includes rows where generated_by is NULL
    res = sb.table('questions').select('*').or_('generated_by.is.null,generated_by.neq.entity_rewriter').limit(batch_size).execute()
    
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

Output MUST be ONLY a valid JSON object (no markdown, no backticks):
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
            continue
            
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                sb.table('questions').update({
                    'question_en': data['question_en'],
                    'options_en': data['options_en'],
                    'explanation': data['explanation'],
                    'generated_by': 'entity_rewriter'
                }).eq('id', q['id']).execute()
                print(f"  ✅ Updated {q['id']} (via {used_model})")
            else:
                print(f"  ⚠️ Failed to parse JSON for {q['id']}")
        except Exception as e:
            print(f"  🚨 Error on {q['id']}: {e}")
        
        time.sleep(1)

    return True

if __name__ == "__main__":
    print("🚀 Starting continuous batch rewrite...")
    total = 0
    while True:
        success = rewrite_batch(batch_size=5)
        if not success:
            print(f"🎉 ALL DONE! Total questions processed in this run: {total}")
            break
        total += 5
        sys.stdout.flush()
