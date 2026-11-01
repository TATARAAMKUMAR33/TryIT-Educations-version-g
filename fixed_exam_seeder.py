import os, json, time, re
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

def call_ai(prompt):
    # 1. Groq
    if groq:
        try:
            print(f"      🧠 Asking Groq...")
            resp = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=4000, timeout=30
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ Groq failed: {str(e)[:80]}")

    # 2. Gemini
    if gemini:
        try:
            print(f"      🧠 Asking Gemini...")
            resp = gemini.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.text.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ Gemini failed: {str(e)[:80]}")

    # 3. NVIDIA
    if nvidia:
        try:
            print(f"      🧠 Asking NVIDIA...")
            resp = nvidia.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=4000, timeout=30
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ NVIDIA failed: {str(e)[:80]}")

    return None

print("⏳ Fetching valid topics...")
valid_topics = [t['topic_id'] for t in s.table('topics').select('topic_id').execute().data]
valid_topics_str = ", ".join(valid_topics[:100]) 

TARGET_EXAMS = [
    "CAT (MBA Entrance)", "XAT", "CMAT", "MAT", "NMAT", "SNAP", "Executive MBA", "Online MBA", "Distance MBA",
    "SSC CGL", "SSC CHSL", "SSC MTS", "SSC GD Constable", "SSC CPO", "SSC JE", 
    "IBPS PO", "IBPS Clerk", "SBI PO", "SBI Clerk", "RBI Grade B", "NABARD Grade A",
    "RRB NTPC", "RRB Group D", "RRB JE", "RRB ALP",
    "TNPSC Group 1", "TNPSC Group 2", "TNPSC Group 4", "UPPSC PCS", "MPSC State Services", "BPSC CCE", "RPSC RAS", "WBPSC WBCS", "KPSC KAS", "MPPSC",
    "NDA", "CDS", "AFCAT", "Indian Army Agniveer", "Indian Navy Agniveer", "Indian Air Force Agniveer", "CAPF AC", "State Police SI",
    "CBSE Class 10 Board", "CBSE Class 12 Board", "ICSE Class 10 Board", "ISC Class 12 Board",
    "Navodaya JNVST Class 6", "Sainik School AISSEE Class 6", "NTSE", "NMMS", "SOF IMO Class 1-5", "SOF NSO Class 1-5",
    "JEE Main", "JEE Advanced", "NEET-UG", "CUET-UG", "CLAT-UG", "NIFT", "NATA", "UCEED", "GATE", "CUET-PG", "UGC-NET", "CSIR-NET", "NEET-PG",
    "AYUSH Entrance", "Physiotherapy Entrance", "Nursing Entrance", "Pharmacy Entrance", "Veterinary Entrance",
    "CA Foundation", "CA Inter", "CA Final", "CS CSEET", "CMA", "NISM Series", "IRDAI Agent", "FSSAI FoSTaC",
    "TCS NQT", "Infosys InfyTQ", "Wipro Elite NTH", "Accenture Hiring", "AMCAT", "CoCubes",
    "IELTS", "TOEFL", "PTE", "GRE", "GMAT", "USMLE", "PLAB"
]

def get_prompt(exam_name):
    return f"""
You are the Chief Exam Architect. 
Generate the exact exam pattern for: "{exam_name}".
Map sections to our valid topics. Do NOT invent new topic_ids. Valid topics include: {valid_topics_str}, etc.
CRITICAL RULES:
1. For Class 1-8 exams, negative_marking must be 0.0.
2. For competitive exams (SSC, UPSC, GATE, CAT), use real negative markings (0.25, 0.33, 0.50, 1.0).
3. Include cutoff marks and PYQ notes.
Output MUST be a valid JSON object with an "exams" array.

Format:
{{
  "exams": [
    {{
      "exam_id": "unique_slug",
      "exam_name": "{exam_name}",
      "conducting_body": "Body",
      "category": "school/higher_ed/govt/corporate/professional",
      "qualification_level": "10th/12th/graduate",
      "tiers": [
        {{
          "tier_id": "unique_slug_tier1",
          "tier_name": "Paper 1 / Prelims",
          "is_qualifying": false,
          "total_questions": 100,
          "total_marks": 200,
          "duration_minutes": 60,
          "negative_marking_rate": 0.25,
          "cutoff_general": 150,
          "pyq_notes": "Frequently asks formula-based questions.",
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

for exam_name in TARGET_EXAMS:
    print(f"\n🌍 Generating: {exam_name}")
    exams_data = call_ai(get_prompt(exam_name))
    
    if not exams_data:
        print(f"  ❌ Failed for {exam_name}. Skipping...")
        time.sleep(10) # Sleep even on failure to reset limits
        continue
        
    for exam in exams_data:
        exam_id = exam.get("exam_id")
        if not exam_id: continue
        
        try:
            s.table('exam_registry').upsert({
                "exam_id": exam_id, "exam_name": exam.get("exam_name"),
                "conducting_body": exam.get("conducting_body"), "category": exam.get("category"),
                "qualification_level": exam.get("qualification_level"), "research_status": "deep_dived"
            }).execute()
            
            for tier in exam.get("tiers", []):
                tier_id = tier.get("tier_id")
                tier_data = {
                    "tier_id": tier_id, "exam_id": exam_id, "tier_name": tier.get("tier_name"),
                    "is_qualifying": tier.get("is_qualifying", False), "total_questions": tier.get("total_questions"),
                    "total_marks": tier.get("total_marks"), "duration_minutes": tier.get("duration_minutes"),
                    "negative_marking_rate": tier.get("negative_marking_rate"), "mode": "online_cbt"
                }
                
                # Safely try to add cutoff and pyq if the columns exist
                if "cutoff_general" in tier: tier_data["cutoff_general"] = tier.get("cutoff_general")
                if "pyq_notes" in tier: tier_data["pyq_notes"] = tier.get("pyq_notes")
                
                try:
                    s.table('exam_tiers').upsert(tier_data).execute()
                except Exception as db_err:
                    if "cutoff_general" in str(db_err):
                        # Fallback if column doesn't exist yet
                        del tier_data["cutoff_general"]
                        del tier_data["pyq_notes"]
                        s.table('exam_tiers').upsert(tier_data).execute()
                
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
        except Exception as e:
            print(f"    ⚠️ DB Error: {str(e)[:100]}")
            
    print("    ⏳ Sleeping 10s to prevent rate limit...")
    time.sleep(10) 

print("\n🎉 FIXED EXAM SEEDER COMPLETE!")
