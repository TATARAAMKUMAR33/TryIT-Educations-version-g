import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("🔍 SCANNING DATABASE FOR EXPLANATION QUALITY...")
qs = s.table('questions').select('id, topic_id, explanation').execute().data

total = len(qs)
bad_stories = 0
bad_intel = 0

for q in qs:
    expl = q.get('explanation') or {}
    story = expl.get('story_explanation', '').lower()
    intel = expl.get('cross_exam_intelligence', '').lower()
    
    # Check if the story is theoretical or missing
    if "imagine" in story or "this is useful" in intel or len(story) < 20 or len(intel) < 20:
        bad_stories += 1
        bad_intel += 1

print("=" * 50)
print(f"📊 TOTAL QUESTIONS: {total}")
print(f"✅ GOOD EXPLANATIONS: {total - bad_stories}")
print(f"❌ BAD/MISSING EXPLANATIONS: {bad_stories}")
print("=" * 50)
print("If 'BAD' is high, run the fix_explanations.py script.")
