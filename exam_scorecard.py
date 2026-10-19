import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

total = s.table('exams').select('id', count='exact').execute().count
flagged = s.table('exams').select('id', count='exact').eq('needs_verification', True).execute().count
verified = total - flagged

# Get category breakdown
exams = s.table('exams').select('category').execute().data
from collections import Counter
cats = Counter(e['category'] for e in exams if e.get('category'))

report = f"""📊 TRYIT EXAM UNIVERSE SCORECARD 📊

📈 Total Exams: {total}
✅ Verified: {verified}
⚠️ Needs Review: {flagged}

📁 Coverage by Category:
"""
for cat, count in cats.most_common(10):
    report += f"  • {cat.title()}: {count}\n"

print(report)
with open('/tmp/scorecard.txt', 'w') as f:
    f.write(report)
