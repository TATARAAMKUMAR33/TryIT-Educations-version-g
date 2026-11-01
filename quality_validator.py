import os, requests, json
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {'apikey': k, 'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}

print("🤖 Starting Automated Quality Validator...")

# 1. Fetch questions that are pending human QA
r = requests.get(f'{u}/rest/v1/questions?select=*&generated_by=eq.tryit_v3&limit=100', headers=h).json()

if not r:
    print("✅ No pending questions to validate.")
    exit()

print(f"Checking {len(r)} questions...\n")

broken_count = 0
passed_count = 0

for q in r:
    is_valid = True
    errors = []

    # Rule 1: Must have exactly 4 options
    if not q.get('options_en') or len(q['options_en']) != 4:
        is_valid = False
        errors.append("Missing options")

    # Rule 2: Correct answer must be an integer between 0 and 3
    if not isinstance(q.get('correct_answer'), int) or q['correct_answer'] not in [0, 1, 2, 3]:
        is_valid = False
        errors.append("Invalid answer index")

    exp = q.get('explanation', {})
    if not isinstance(exp, dict):
        is_valid = False
        errors.append("Explanation is not a dictionary")
    else:
        # Rule 3: Why correct must exist and mention the option
        why_correct = exp.get('why_correct', '')
        if len(why_correct) < 20:
            is_valid = False
            errors.append("Explanation too short or missing")
            
        # Rule 4: Story must exist (Indian context)
        if not exp.get('story_explanation') or len(exp.get('story_explanation', '')) < 30:
            is_valid = False
            errors.append("Missing or short story")

    # Take action based on validation
    if not is_valid:
        broken_count += 1
        print(f"❌ Rejected {q['id']}: {', '.join(errors)}")
        # Move to bot_rejected so humans don't waste time
        requests.patch(f"{u}/rest/v1/questions?id=eq.{q['id']}", headers=h, json={
            "generated_by": "tryit_v3_bot_rejected",
            "review_notes": f"AUTO-BOT REJECTED: {', '.join(errors)}"
        })
    else:
        passed_count += 1
        # Mark as 'ready_for_human' so QA team knows it passed the robot
        requests.patch(f"{u}/rest/v1/questions?id=eq.{q['id']}", headers=h, json={
            "generated_by": "tryit_v3_ready_for_human"
        })

print(f"\n🎉 Validation Complete: {passed_count} passed, {broken_count} rejected.")
