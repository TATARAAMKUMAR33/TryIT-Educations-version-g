import os
import requests
import json
import time
from collections import Counter

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()
AZURE_KEY = os.environ.get("AZURE_API_KEY", "").strip()
AZURE_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("🕵️ Starting V8 LLM Fixer (Generating Staged Fixes)...", flush=True)
print("🛑 DATABASE WILL NOT BE MODIFIED. Output will be saved as JSON.\n", flush=True)

staged_fixes = []
total_scanned = 0
limit = 500
offset = 0

# We only want to process a small batch first to test the API!
# We will change this to fetch all 6,149 once the test works.
MAX_FIXES_PER_RUN = 5 

print(f"⚠️ TEST MODE: Only fixing the first {MAX_FIXES_PER_RUN} broken questions to verify API connection.", flush=True)

while True:
    if len(staged_fixes) >= MAX_FIXES_PER_RUN:
        break

    print(f"📥 Fetching rows {offset} to {offset + limit}...", flush=True)
    res = requests.get(
        f'{SUPABASE_URL}/rest/v1/questions?select=id,question_en,options_en,correct_answer,explanation&limit={limit}&offset={offset}', 
        headers=headers, timeout=30
    )
    questions = res.json()
    if not questions:
        break

    for q in questions:
        if len(staged_fixes) >= MAX_FIXES_PER_RUN:
            break
            
        total_scanned += 1
        exp = q.get('explanation', {})
        opts = q.get('options_en', [])
        
        # Check if it fails Gate 1 or Gate 2
        is_broken = False
        if not isinstance(exp, dict) or len(opts) != 4:
            is_broken = True
        else:
            layers = [exp.get(layer, '') for layer in ['why_correct', 'story_explanation', 'shortcut_tips', 'cross_exam_intelligence', 'why_wrong_option_b', 'why_wrong_option_c', 'why_wrong_option_d']]
            if any(len(layer) < 50 for layer in layers):
                is_broken = True

        if not is_broken:
            continue

        # FOUND A BROKEN QUESTION. SEND TO LLM.
        print(f"🔧 Fixing Question ID: {q['id']}...", flush=True)
        
        # --- LLM CALL (Azure OpenAI Example) ---
        # Note: You may need to adjust the URL and payload based on your exact Azure deployment
        if AZURE_KEY and AZURE_ENDPOINT:
            llm_url = f"{AZURE_ENDPOINT}/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview"
            llm_headers = {"api-key": AZURE_KEY, "Content-Type": "application/json"}
            
            prompt = f"""
            Fix the explanation for this question. 
            Question: {q['question_en']}
            Options: {opts}
            Correct Answer Index: {q['correct_answer']}
            Current Explanation: {json.dumps(exp)}
            
            Return ONLY a valid JSON object with exactly these keys: 
            'why_correct', 'story_explanation', 'shortcut_tips', 'cross_exam_intelligence', 'why_wrong_option_b', 'why_wrong_option_c', 'why_wrong_option_d'.
            Every value must be a string longer than 60 characters.
            """
            
            payload = {
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            
            try:
                llm_res = requests.post(llm_url, headers=llm_headers, json=payload, timeout=60)
                if llm_res.status_code == 200:
                    new_exp_text = llm_res.json()['choices'][0]['message']['content']
                    # Clean markdown formatting if LLM adds it
                    new_exp_text = new_exp_text.replace("```json", "").replace("```", "").strip()
                    new_exp = json.loads(new_exp_text)
                    
                    staged_fixes.append({
                        "id": q['id'],
                        "old_explanation": exp,
                        "new_explanation": new_exp
                    })
                    print(f"  ✅ Successfully fixed ID {q['id']}", flush=True)
                else:
                    print(f"  ❌ LLM Error: {llm_res.status_code} - {llm_res.text}", flush=True)
            except Exception as e:
                print(f"  ❌ LLM Exception: {e}", flush=True)
        else:
            print("  ❌ No AZURE_API_KEY or ENDPOINT found in environment variables.", flush=True)
            break

    offset += limit
    time.sleep(0.5)

# Save to JSON file for GitHub Artifact
if staged_fixes:
    with open("staged_fixes.json", "w", encoding="utf-8") as f:
        json.dump(staged_fixes, f, indent=4)
    print(f"\n✅ Saved {len(staged_fixes)} fixes to staged_fixes.json", flush=True)
else:
    print("\n⚠️ No fixes were staged.", flush=True)
