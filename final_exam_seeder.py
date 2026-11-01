import os, json, time, re
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
import json_repair

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

GROQ_KEY = os.getenv("GROQ_API_KEY_1")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY_1")

groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY) if GROQ_KEY else None
nvidia = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY) if NVIDIA_KEY else None

def call_ai(prompt):
    for name, client in [("Groq", groq), ("NVIDIA", nvidia)]:
        if not client: continue
        try:
            print(f"      🧠 Asking {name}...")
            model = "openai/gpt-oss-120b" if name == "Groq" else "nvidia/nemotron-3-super-120b-a12b"
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=4000, timeout=45
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ {name} failed: {str(e)[:80]}")
    return None

print("⏳ Fetching valid topics...")
valid_topics = [t['topic_id'] for t in s.table('topics').select('topic_id').execute().data]
valid_topics_str = ", ".join(valid_topics[:100]) 

# 🚨 THE EXACT HARDCODED LIST (No more AI laziness)
TARGET_EXAMS = [
    # MBA Variants
    "CAT (MBA Entrance)", "XAT", "CMAT", "MAT", "NMAT", "SNAP", "Executive MBA", "Online MBA", "Distance MBA",
    # Central Govt (SSC & Banking)
    "SSC CGL", "SSC CHSL", "SSC MTS", "SSC GD Constable", "SSC CPO", "SSC JE", 
    "IBPS PO", "IBPS Clerk", "SBI PO", "SBI Clerk", "RBI Grade B", "NABARD Grade A",
    # Railways
    "RRB NTPC", "RRB Group D", "RRB JE", "RRB ALP",
    # State PSCs (Top 10)
    "TNPSC Group 1", "TNPSC Group 2", "TNPSC Group 4", "UPPSC PCS", "MPSC State Services", "BPSC CCE", "RPSC RAS", "WBPSC WBCS", "KPSC KAS", "MPPSC",
    # Defence & Police
    "NDA", "CDS", "AFCAT", "Indian Army Agniveer", "Indian Navy Agniveer", "Indian Air Force Agniveer", "CAPF AC", "State Police SI",
    # School Boards (Specific Classes)
    "CBSE Class 10 Board", "CBSE Class 12 Board", "ICSE Class 10 Board", "ISC Class 12 Board",
    # School Entrances & Scholarships
    "Navodaya JNVST Class 6", "Sainik School AISSEE Class 6", "NTSE", "NMMS", "SOF IMO Class 1-5", "SOF NSO Class 1-5",
    # Higher Ed Entrances
    "JEE Main", "JEE Advanced", "NEET-UG", "CUET-UG", "CLAT-UG", "NIFT", "NATA", "UCEED", "GATE", "CUET-PG", "UGC-NET", "CSIR-NET", "NEET-PG",
    # Medical & Allied Health
    "AYUSH Entrance", "Physiotherapy Entrance", "Nursing Entrance", "Pharmacy Entrance", "Veterinary Entrance",
    # Professional & Corporate
    "CA Foundation", "CA Inter", "CA Final", "CS CSEET", "CMA", "NISM Series", "IRDAI Agent", "FSSAI FoSTaC",
    "TCS NQT", "Infosys InfyTQ", "Wipro Elite NTH", "Accenture Hiring", "AMCAT", "CoCubes",
    # Foreign & Language
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
4. Output MUST be a valid JSON object with an "exams" array.

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
        time.sleep(3)
        continue
        
    for exam in exams_data:
        exam_id = exam.get("exam_id")
        if not exam_id: continue
        
        try:
            # 1. Exam Registry
            s.table('exam_registry').upsert({
                "exam_id": exam_id, "exam_name": exam.get("exam_name"),
                "conducting_body": exam.get("conducting_body"), "category": exam.get("category"),
                "qualification_level": exam.get("qualification_level"), "research_status": "deep_dived"
            }).execute()
            
            # 2. Tiers & Sections
            for tier in exam.get("tiers", []):
                tier_id = tier.get("tier_id")
                s.table('exam_tiers').upsert({
                    "tier_id": tier_id, "exam_id": exam_id, "tier_name": tier.get("tier_name"),
                    "is_qualifying": tier.get("is_qualifying", False), "total_questions": tier.get("total_questions"),
                    "total_marks": tier.get("total_marks"), "duration_minutes": tier.get("duration_minutes"),
                    "negative_marking_rate": tier.get("negative_marking_rate"), "mode": "online_cbt",
                    "cutoff_general": tier.get("cutoff_general"),
                    "pyq_notes": tier.get("pyq_notes")
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
        except Exception as e:
            print(f"    ⚠️ DB Error: {str(e)[:100]}")
            
    time.sleep(2) 

print("\n🎉 HARDCODED MASTER SEEDING COMPLETE!")
