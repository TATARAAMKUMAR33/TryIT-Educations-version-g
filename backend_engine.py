import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

# 1. ZERO-ERROR DB INSERT (Auto-Retry)
def safe_db_insert(supabase_client, table_name, data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = supabase_client.table(table_name).insert(data).execute()
            return True, response
        except Exception as e:
            print(f"⚠️ DB Insert Failed (Attempt {attempt+1}/{max_retries}): {e}")
            time.sleep(2)
    return False, None

# 2. SMART DEDUPLICATION (Prevents wasting credits)
def is_duplicate(supabase_client, question_text, topic_id):
    try:
        # Check for exact or highly similar question in the same topic
        # Using a simple substring match for speed, but you could use pgvector for semantic search
        safe_text = question_text[:50].replace("'", "''")
        response = supabase_client.table('questions').select('id').eq('topic_id', topic_id).ilike('question_en', f'%{safe_text}%').limit(1).execute()
        return len(response.data) > 0
    except Exception:
        return False

# 3. CONCURRENT JSON EXTRACTION (Speed)
def extract_json_array_robust(text):
    if not text: return None
    text = re.sub(r'^```json\s*|\s*```$', '', text.strip(), flags=re.MULTILINE).strip()
    for cand in [text, text[text.find('['):text.rfind(']')+1] if '[' in text else text]:
        if not cand: continue
        try:
            import json
            d = json.loads(cand)
            if isinstance(d, list): return d
        except Exception:
            try:
                import json_repair
                d = json_repair.loads(cand)
                if isinstance(d, list): return d
            except Exception: continue
    return None

# 4. PARALLEL VERIFICATION (5x Speed)
async def verify_questions_parallel(questions, verify_func, level):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=5) as pool:
        tasks = [
            loop.run_in_executor(pool, verify_func, q, level) 
            for q in questions
        ]
        results = await asyncio.gather(*tasks)
    return results
