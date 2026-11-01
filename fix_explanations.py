import os, json, time, re, random
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

GROQ_KEY = os.getenv("GROQ_API_KEY_1")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_API_KEY_1")

groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY) if GROQ_KEY else None
nvidia = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY) if NVIDIA_KEY else None
gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# 🚨 UNLIMITED DIVERSITY POOL
NAMES = ["Ramu", "Priya", "Abdul", "Kavitha", "Sundar", "Meena", "Rahul", "Anjali", "Vikram", "Sneha", "Ravi", "Kiran", "Fatima", "Arjun", "Divya", "Amit", "Pooja", "Sanjay", "Neha", "Karthik"]
CITIES = ["Chennai", "Mumbai", "Delhi", "Kolkata", "Bangalore", "Hyderabad", "Karur", "Coimbatore", "Madurai", "Pune", "Jaipur", "Lucknow", "Patna", "Bhopal", "Kochi"]
SCENARIOS = ["splitting an auto-rickshaw fare", "buying vegetables at the local shandy market", "calculating discount during a sale", "splitting a restaurant bill", "calculating daily profit at a tea stall", "packing tiffin boxes for a trip", "dividing a chit fund payout", "estimating bricks for a wall", "comparing mobile recharge plans", "calculating marks needed to pass"]

def get_prompt(q_text, correct_opt, topic_id, level):
    name = random.choice(NAMES)
    city = random.choice(CITIES)
    scenario = random.choice(SCENARIOS)
    
    return f"""
You are an expert Indian exam mentor.
Rewrite the explanation for this question.

Question: {q_text}
Correct Option: {correct_opt}
Topic: {topic_id}
Level: {level}

You MUST return a JSON object with exactly these two keys:
1. "story_explanation": Write a 2-3 sentence relatable story using the character "{name}" from "{city}" who is {scenario}. The story MUST explain why the correct answer is right in a conversational, human way. Do NOT use theoretical jargon or "Imagine a..." phrasing.
2. "cross_exam_intelligence": Specifically list 3-5 real exams where this exact question appears (e.g., "SSC CGL Tier 1, IBPS PO, RRB NTPC, Class 10 CBSE") and state the difficulty level it is asked at (e.g., "Asked at Level 5-6").

Return ONLY JSON:
{{
  "story_explanation": "...",
  "cross_exam_intelligence": "..."
}}
"""

def call_ai(prompt):
    # 1. Groq
    if groq:
        try:
            resp = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=1000, timeout=20
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            return json_repair.loads(raw)
        except Exception as e: print(f"      ⚠️ Groq failed: {str(e)[:60]}")

    # 2. Gemini
    if gemini:
        try:
            resp = gemini.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.text.strip(), flags=re.MULTILINE).strip()
            return json_repair.loads(raw)
        except Exception as e: print(f"      ⚠️ Gemini failed: {str(e)[:60]}")

    # 3. NVIDIA
    if nvidia:
        try:
            resp = nvidia.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=1000, timeout=20
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            return json_repair.loads(raw)
        except Exception as e: print(f"      ⚠️ NVIDIA failed: {str(e)[:60]}")

    return None

print("⏳ Fetching all bad questions...")
# Fetch all questions and filter for the bad ones
all_qs = []
offset = 0
while True:
    batch = s.table('questions').select('id, topic_id, level, question_en, options_en, correct_answer, explanation').range(offset, offset + 999).execute().data
    if not batch: break
    for q in batch:
        expl = q.get('explanation') or {}
        story = expl.get('story_explanation', '').lower()
        intel = expl.get('cross_exam_intelligence', '').lower()
        if "imagine" in story or "this is useful" in intel or len(story) < 20 or len(intel) < 20:
            all_qs.append(q)
    if len(batch) < 1000: break
    offset += 1000

print(f"🔍 Found {len(all_qs)} bad questions to fix.\n")

for i, q in enumerate(all_qs):
    print(f"[{i+1}/{len(all_qs)}] Fixing: {q['question_en'][:40]}...")
    
    q_text = q['question_en']
    correct_opt = q['options_en'][q['correct_answer']]
    
    prompt = get_prompt(q_text, correct_opt, q['topic_id'], q['level'])
    new_data = call_ai(prompt)
    
    if new_data and "story_explanation" in new_data:
        expl = q['explanation'] or {}
        expl['story_explanation'] = new_data['story_explanation']
        expl['cross_exam_intelligence'] = new_data['cross_exam_intelligence']
        
        s.table('questions').update({"explanation": expl}).eq('id', q['id']).execute()
        print("   ✅ Fixed")
    else:
        print("   ❌ Failed to generate new explanation")
        
    time.sleep(2) # Prevents rate limits

print("\n🎉 ALL 579 BAD EXPLANATIONS FIXED!")
