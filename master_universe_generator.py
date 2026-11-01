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
    # Try Groq first (fastest for JSON)
    if groq:
        try:
            print(f"      🧠 Asking Groq...")
            resp = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=4000, timeout=40
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ Groq failed: {str(e)[:80]}")

    # Try NVIDIA
    if nvidia:
        try:
            print(f"      🧠 Asking NVIDIA...")
            resp = nvidia.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=4000, timeout=40
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ NVIDIA failed: {str(e)[:80]}")

    # Try Gemini
    if gemini:
        try:
            print(f"      🧠 Asking Gemini...")
            resp = gemini.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.text.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ Gemini failed: {str(e)[:80]}")

    return None

print("⏳ Fetching valid topics...")
valid_topics = [t['topic_id'] for t in s.table('topics').select('topic_id').execute().data]
valid_topics_str = ", ".join(valid_topics[:100]) 

# 🚨 THE EXHAUSTIVE BATCHES (Covering Class 1 to Senior, National to State)
batches = [
    # School Boards & Entrance
    ["CBSE Class 1-5", "CBSE Class 6-8", "CBSE Class 9-10", "CBSE Class 11-12"],
    ["ICSE Class 1-5", "ICSE Class 6-8", "ICSE Class 9-10", "ISC Class 11-12"],
    ["IB PYP (Class 1-5)", "IB MYP (Class 6-10)", "IB DP (Class 11-12)", "Cambridge IGCSE", "Cambridge AS/A Level"],
    ["Navodaya JNVST Class 6", "Navodaya JNVST Class 9", "Sainik School AISSEE Class 6", "Sainik School AISSEE Class 9"],
    ["NTSE", "NMMS", "SOF IMO", "SOF NSO", "HBCSE Olympiads"],
    
    # State Boards (Top States)
    ["Tamil Nadu State Board Class 10", "Tamil Nadu State Board Class 12"],
    ["Maharashtra State Board Class 10", "Maharashtra State Board Class 12"],
    ["UP State Board Class 10", "UP State Board Class 12"],
    ["Karnataka State Board Class 10", "Karnataka State Board Class 12"],
    ["Kerala State Board Class 10", "Kerala State Board Class 12"],
    
    # Higher Education Entrances
    ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE"],
    ["NEET-UG", "AIIMS Nursing", "AFMC"],
    ["CUET-UG", "CUET-PG", "IPMAT", "NPAT"],
    ["CLAT", "AILET", "LSAT India"],
    ["NIFT", "NID", "UCEED", "CEED", "NATA"],
    
    # PG & Research
    ["GATE", "IIT JAM", "CSIR-NET", "UGC-NET"],
    ["CAT", "XAT", "CMAT", "MAT", "SNAP", "NMAT"],
    ["NEET-PG", "INI-CET"],
    
    # Central Govt Jobs
    ["UPSC CSE Prelims", "UPSC CSE Mains", "UPSC CDS", "UPSC CAPF", "UPSC ESE"],
    ["SSC CGL", "SSC CHSL", "SSC MTS", "SSC GD Constable", "SSC CPO", "SSC JE"],
    ["IBPS PO", "IBPS Clerk", "SBI PO", "SBI Clerk", "RBI Grade B"],
    ["RRB NTPC", "RRB Group D", "RRB JE", "RRB ALP"],
    ["NDA", "AFCAT", "Indian Army Agniveer", "Indian Navy Agniveer"],
    
    # State PSCs (Exhaustive)
    ["TNPSC Group 1", "TNPSC Group 2", "TNPSC Group 4", "TNPSC VAO"],
    ["UPPSC PCS", "BPSC CCE", "MPSC State Services", "RPSC RAS"],
    ["WBPSC WBCS", "GPSC Class 1-2", "KPSC KAS", "MPPSC State Service"],
    ["OPSC OCS", "HPPSC HAS", "UKPSC", "JK PSC"],
    ["APPSC Group 1", "TSPSC Group 1", "Kerala PSC", "Assam PSC"],
    
    # State Departmental & TETs
    ["CTET", "TNTET", "UPTET", "BTET", "KTET"],
    ["State Police SI", "State Police Constable", "State Forest Guard"],
    ["State Judicial Service (Civil Judge)"],
    
    # Corporate & IT
    ["TCS NQT", "Infosys InfyTQ", "Wipro Elite NTH", "Accenture Hiring"],
    ["Cognizant GenC", "Capgemini", "HCL TechBee", "AMCAT", "CoCubes"],
    
    # Foreign Study & Professional
    ["IELTS", "TOEFL", "PTE", "GRE", "GMAT", "SAT"],
    ["USMLE", "PLAB", "NCLEX"],
    ["CA Foundation", "CA Inter", "CA Final", "CS CSEET", "CMA"],
    ["NISM Series", "IRDAI", "FSSAI FoSTaC"],
    ["AWS Cloud Practitioner", "Microsoft Azure", "Cisco CCNA", "PMP"]
]

def get_prompt(exam_batch):
    batch_str = ", ".join(exam_batch)
    return f"""
You are the Chief Exam Architect. 
Generate the exact exam pattern for these specific exams: {batch_str}.
Map sections to our valid topics. Do NOT invent new topic_ids. Valid topics include: {valid_topics_str}, etc.

CRITICAL RULES:
1. For Class 1-8 exams, negative_marking must be 0.0.
2. For Class 10-12 boards, negative_marking is usually 0.0.
3. For competitive exams (SSC, UPSC, GATE, CAT), use real negative markings (0.25, 0.33, 0.50, 1.0).
4. Include cutoff marks and PYQ notes.
5. Output MUST be a valid JSON object with an "exams" array.

Format:
{{
  "exams": [
    {{
      "exam_id": "unique_slug",
      "exam_name": "Exact Name",
      "conducting_body": "Body",
      "category": "school/higher_ed/govt/corporate",
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

for batch in batches:
    print(f"\n🌍 Processing Batch: {', '.join(batch)}")
    
    exams_data = call_ai(get_prompt(batch))
    
    if not exams_data:
        print(f"  ❌ Failed for batch. Skipping...")
        time.sleep(5)
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
            
    print("    ⏳ Sleeping for 5 seconds to avoid rate limits...")
    time.sleep(5) 

print("\n🎉 MASTER EXAM UNIVERSE GENERATION COMPLETE!")
