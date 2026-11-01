"""
TryIT Auto-Exam Generator v2
Uses NVIDIA, Groq, and Gemini with strict timeouts to prevent hanging.
"""
import os, json, time, re
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# ── AI CLIENTS ──
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY_1")
GROQ_KEY = os.getenv("GROQ_API_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_API_KEY_1")

nvidia = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY) if NVIDIA_KEY else None
groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY) if GROQ_KEY else None
gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def call_ai(prompt):
    """Failover between NVIDIA, Groq, and Gemini with strict timeouts."""
    
    # 1. Try NVIDIA
    if nvidia:
        try:
            print(f"      🧠 Asking NVIDIA...")
            resp = nvidia.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=4000,
                timeout=25 # STRICT TIMEOUT
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e:
            print(f"      ⚠️ NVIDIA failed/timed out: {str(e)[:80]}")

    # 2. Try Groq
    if groq:
        try:
            print(f"      🧠 Asking Groq...")
            resp = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.2, max_tokens=4000,
                timeout=25 # STRICT TIMEOUT
            )
            raw = resp.choices[0].message.content.strip()
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e:
            print(f"      ⚠️ Groq failed/timed out: {str(e)[:80]}")

    # 3. Try Gemini
    if gemini:
        try:
            print(f"      🧠 Asking Gemini...")
            resp = gemini.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            raw = resp.text.strip()
            raw = re.sub(r'^```json\s*|\s*```$', '', raw, flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e:
            print(f"      ⚠️ Gemini failed: {str(e)[:80]}")

    return None

# ── FETCH VALID TOPICS ──
print("⏳ Fetching valid topics from database...")
valid_topics = [t['topic_id'] for t in s.table('topics').select('topic_id').execute().data]
valid_topics_str = ", ".join(valid_topics[:100]) 
print(f"✅ Loaded {len(valid_topics)} topics.")

categories_to_process = [
    "State Public Service Commissions (TNPSC, UPPSC, MPSC, BPSC, etc.)",
    "State Police & Departmental Exams (SI, Constable, TET, Forest Guard)",
    "Central Government (UPSC, SSC CGL, SSC CHSL, SSC MTS, RRB, Defence)",
    "Banking & Finance (IBPS PO, Clerk, SBI, RBI, NABARD, LIC)",
    "School Boards (CBSE, ICSE, State Boards for Class 10 and 12)",
    "School Entrances & Scholarships (Sainik, Navodaya, NTSE, Olympiads)",
    "Entrance Exams (JEE, NEET, CLAT, NIFT, NATA, CUET, BBA)",
    "Corporate & Private Companies (TCS NQT, Infosys, Wipro, Accenture)",
    "Foreign Study (IELTS, TOEFL, GRE, GMAT, USMLE, PLAB)"
]

def get_prompt(category):
    return f"""
You are building the Exam Universe for TryIT Educations.
Generate exact exam data for: "{category}".
Map sections to our valid topics. Do NOT invent new topic_ids. 
Valid topics include: {valid_topics_str}, etc.
Negative marking must be a decimal (e.g., 0.25, 0.50, 0.333, or 0.0).
Output MUST be a valid JSON object with an "exams" array.

Format:
{{
  "exams": [
    {{
      "exam_id": "unique_slug",
      "exam_name": "Exact Name",
      "conducting_body": "Body",
      "category": "{category}",
      "qualification_level": "10th/12th/graduate",
      "tiers": [
        {{
          "tier_id": "unique_slug_tier1",
          "tier_name": "Tier 1",
          "is_qualifying": false,
          "total_questions": 100,
          "total_marks": 200,
          "duration_minutes": 60,
          "negative_marking_rate": 0.25,
          "sections": [
            {{
              "section_id": "unique_slug_tier1_quant",
              "section_name": "Quantitative Aptitude",
              "num_questions": 25,
              "marks_per_question": 2.0,
              "subject_group": "quant",
              "topics": [{{"topic_id": "maths_arithmetic_percentage", "weightage": 10}}]
            }}
          ]
        }}
      ]
    }}
  ]
}}
"""

for category in categories_to_process:
    print(f"\n🚀 Processing Category: {category}")
    exams_data = call_ai(get_prompt(category))
    
    if not exams_data:
        print(f"  ❌ Failed to generate data for {category}.")
        continue
        
    print(f"  📥 Generated {len(exams_data)} exams. Pushing to Supabase...")
    
    for exam in exams_data:
        exam_id = exam.get("exam_id")
        if not exam_id: continue
        
        try:
            s.table('exam_registry').upsert({
                "exam_id": exam_id,
                "exam_name": exam.get("exam_name"),
                "conducting_body": exam.get("conducting_body"),
                "category": exam.get("category"),
                "qualification_level": exam.get("qualification_level"),
                "research_status": "deep_dived"
            }).execute()
            
            for tier in exam.get("tiers", []):
                tier_id = tier.get("tier_id")
                s.table('exam_tiers').upsert({
                    "tier_id": tier_id, "exam_id": exam_id, "tier_name": tier.get("tier_name"),
                    "is_qualifying": tier.get("is_qualifying", False), "total_questions": tier.get("total_questions"),
                    "total_marks": tier.get("total_marks"), "duration_minutes": tier.get("duration_minutes"),
                    "negative_marking_rate": tier.get("negative_marking_rate"), "mode": "online_cbt"
                }).execute()
                
                for section in tier.get("sections", []):
                    section_id = section.get("section_id")
                    s.table('exam_sections').upsert({
                        "section_id": section_id, "tier_id": tier_id, "section_name": section.get("section_name"),
                        "num_questions": section.get("num_questions"), "marks_per_question": section.get("marks_per_question"),
                        "subject_group": section.get("subject_group")
                    }).execute()
                    
                    for mapping in section.get("topics", []):
                        tid = mapping.get("topic_id")
                        if tid not in valid_topics: continue 
                        s.table('exam_syllabus_map').upsert({
                            "map_id": f"{exam_id}_{section_id}_{tid}", "exam_id": exam_id,
                            "section_id": section_id, "topic_id": tid,
                            "weightage_percent": mapping.get("weightage", 10), "priority": 3
                        }).execute()
                        
            print(f"    ✅ Injected: {exam.get('exam_name')}")
            time.sleep(0.5) 
        except Exception as e:
            print(f"    ⚠️ DB Error for {exam_id}: {str(e)[:100]}")
            
    time.sleep(2) 

print("\n🎉 AUTO-EXAM GENERATOR COMPLETE!")
