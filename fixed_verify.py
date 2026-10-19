import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("🔍 SCANNING DATABASE FOR EXPLANATION QUALITY...")

# Get the REAL total count
total_count = s.table('questions').select('id', count='exact').execute().count
print(f"📊 TOTAL QUESTIONS IN DB: {total_count}")

# Fetch in chunks to avoid the 1000 limit
bad_count = 0
fetched = 0
offset = 0
chunk_size = 1000

while True:
    print(f"   Fetching rows {offset} to {offset + chunk_size}...")
    qs = s.table('questions').select('id, explanation').range(offset, offset + chunk_size - 1).execute().data
    if not qs: break
    
    for q in qs:
        expl = q.get('explanation') or {}
        story = expl.get('story_explanation', '').lower()
        intel = expl.get('cross_exam_intelligence', '').lower()
        
        if "imagine" in story or "this is useful" in intel or len(story) < 20 or len(intel) < 20:
            bad_count += 1
            
    fetched += len(qs)
    if fetched >= total_count: break
    offset += chunk_size

print("=" * 50)
print(f"📊 TOTAL QUESTIONS: {total_count}")
print(f"✅ GOOD EXPLANATIONS: {total_count - bad_count}")
print(f"❌ BAD/MISSING EXPLANATIONS: {bad_count}")
print("=" * 50)
