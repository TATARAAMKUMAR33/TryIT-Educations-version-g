import os
import requests
import time
from collections import Counter

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip()

if SUPABASE_KEY.startswith("Bearer "):
    SUPABASE_KEY = SUPABASE_KEY[7:].strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("? ERROR: SUPABASE_URL or SUPABASE_KEY environment variables are missing.")
    exit(1)

headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json'
}

print("??? Starting V8 Fixer Dry-Run (Read-Only)...", flush=True)
print("?? NO DATA WILL BE CHANGED.\n", flush=True)

problems = Counter()
clean_count = 0
total_scanned = 0

limit = 500
offset = 0

while True:
    print(f"?? Fetching rows {offset} to {offset + limit}...", flush=True)
    try:
        res = requests.get(
            f'{SUPABASE_URL}/rest/v1/questions?select=id,question_en,options_en,correct_answer,explanation,subject_id,topic_id&limit={limit}&offset={offset}&order=id.asc', 
            headers=headers, 
            timeout=30 # Prevent infinite hang
        )
    except Exception as e:
        print(f"? Network Error: {e}", flush=True)
        break
        
    if res.status_code != 200:
        print(f"? API Error: {res.status_code} - {res.text}", flush=True)
        break
        
    questions = res.json()
    if not questions:
        print("? Reached end of database.", flush=True)
        break

    for q in questions:
        total_scanned += 1
        exp = q.get('explanation', {})
        opts = q.get('options_en', [])
        ca = q.get('correct_answer', -1)
        
        if not isinstance(exp, dict) or len(opts) != 4 or not isinstance(ca, int):
            problems['Gate 1: Malformed JSON/Structure'] += 1
            continue
            
        layers = [exp.get(layer, '') for layer in ['why_correct', 'story_explanation', 'shortcut_tips', 'cross_exam_intelligence', 'why_wrong_option_b', 'why_wrong_option_c', 'why_wrong_option_d']]
        
        if any(len(layer) < 50 for layer in layers):
            problems['Gate 2: Explanation layer too short (<50 chars)'] += 1
            continue
            
        if len(set(opts)) < 4:
            problems['Gate 3: Duplicate Options found'] += 1
            continue
            
        why_correct = exp.get('why_correct', '').lower()
        correct_letter = ['a', 'b', 'c', 'd'][ca]
        
        wrong_letters_mentioned = [l for l in ['a', 'b', 'c', 'd'] if f"option {l}" in why_correct and l != correct_letter]
        if wrong_letters_mentioned and f"option {correct_letter}" not in why_correct:
            problems['Gate 4: Correct Answer key mismatch'] += 1
            continue
            
        clean_count += 1

    offset += limit
    time.sleep(0.5)

print("\n" + "="*50, flush=True)
print("?? V8 FIXER DRY-RUN REPORT", flush=True)
print("="*50, flush=True)
print(f"Total Scanned: {total_scanned}", flush=True)
print(f"? Truly Clean (Passed Dry-Run): {clean_count}", flush=True)
print(f"?? Failed Dry-Run: {sum(problems.values())}", flush=True)
print("-" * 50, flush=True)
for problem, count in sorted(problems.items()):
    print(f"? {problem}: {count} questions", flush=True)
print("="*50, flush=True)
print("?? NO DATA WAS DELETED OR MODIFIED.", flush=True)
