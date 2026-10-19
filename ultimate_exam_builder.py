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

print("⏳ Fetching valid topics from database...")
valid_topics = [t['topic_id'] for t in s.table('topics').select('topic_id').execute().data]
valid_topics_str = ", ".join(valid_topics[:100]) 

# 🚨 THE EXHAUSTIVE BATCHES (Every detail from your draft is included)
batches = [
    # 1. School Boards & Annual Exams
    ["CBSE Class 1-12", "ICSE Class 1-10", "ISC Class 11-12", "IB PYP/MYP/DP", "Cambridge IGCSE/AS/A Level", "NIOS Open Basic/Secondary/Senior Secondary", "State Boards (TN, MH, UP, KA, KL, AP, TS, WB, GJ, RJ, MP, BR, PB, HR, OD, AS)"],
    
    # 2. School Entrances, Scholarships & Olympiads
    ["Navodaya JNVST Class 6 & 9", "Sainik School AISSEE Class 6 & 9", "RIMC", "NTSE", "NMMS", "INSPIRE (KVPY)", "HBCSE Olympiads", "SOF Olympiads (NSO, IMO, IEO)"],
    
    # 3. After 10th & Skill/Vocational
    ["Polytechnic Entrance", "ITI Admission", "Vocational Admission", "Trade Test", "Apprenticeship Selection", "Recognition of Prior Learning (RPL)", "Skill India Assessment", "Sector Skill Council (SSC) Assessment"],
    
    # 4. UG Entrances (Engineering & Technology)
    ["JEE Main", "JEE Advanced", "BITSAT", "VITEEE", "State CETs (MHT-CET, KCET, WBJEE, AP EAMCET)", "Civil Engineering", "Mechanical Engineering", "Electrical Engineering", "Electronics Engineering", "Chemical Engineering", "Mining Engineering", "Petroleum Engineering", "Metallurgy", "Textile Engineering", "Industrial Engineering", "Robotics", "IoT", "Semiconductor", "GIS", "Geospatial", "Surveying"],
    
    # 5. UG Entrances (Medical & Health)
    ["NEET-UG", "AIIMS Nursing", "Dental", "Nursing", "Medicine", "Pharmacy", "Veterinary", "AYUSH", "Physiotherapy", "Occupational Therapy", "Radiology", "Medical Laboratory", "Optometry", "Paramedical", "Allied Health", "Public Health"],
    
    # 6. UG Entrances (Other Streams)
    ["CLAT-UG", "AILET", "LSAT India", "NIFT", "NID", "UCEED", "CEED", "NATA", "JEE Paper 2", "Hotel Management", "Culinary / Chef", "Hospitality", "Tourism", "Aviation (Pilot, Cabin Crew)", "Maritime (Merchant Navy)", "Law", "Architecture", "Planning", "Design", "Fashion", "Fine Arts", "Music", "Dance", "Theatre", "Film", "Journalism", "Mass Communication", "Social Work", "Psychology", "Education", "Teaching", "Special Education", "Library Science", "Sports", "Physical Education", "Yoga", "Languages", "Translation"],
    
    # 7. PG Entrances & MBA Variants
    ["GATE", "IIT JAM", "CUET-PG", "CAT", "XAT", "CMAT", "MAT", "NMAT", "SNAP", "ATMA", "MBA", "PGDM", "Executive MBA", "Online MBA", "Distance MBA", "Integrated MBA (5-year)", "Specialised MBA", "IIMs", "IIT Management", "Central University MBA", "State University MBA", "Private/Deemed B-Schools", "MA", "MSc", "MCom", "MCA", "MTech", "ME", "MS", "LLM", "MEd", "MPH", "Medical PG", "Dental PG", "Allied Health PG"],
    
    # 8. PhD & Research
    ["UGC-NET", "CSIR-NET", "GATE (PhD)", "JEST", "TIFR-GS", "ICMR-JRF", "ICAR-NET", "JRF", "SRF", "Project Fellow", "Research Assistant"],
    
    # 9. Central Govt Jobs
    ["UPSC CSE (Prelims & Mains)", "UPSC CDS", "UPSC CAPF", "UPSC ESE", "UPSC CMS", "UPSC IFoS", "UPSC IES/ISS", "NDA", "SSC CGL", "SSC CHSL", "SSC MTS", "SSC GD Constable", "SSC CPO", "SSC JE", "SSC Stenographer"],
    
    # 10. Banking & Finance
    ["IBPS PO", "IBPS Clerk", "IBPS SO", "IBPS RRB PO", "IBPS RRB Clerk", "SBI PO", "SBI Clerk", "SBI SO", "RBI Grade B", "RBI Assistant", "NABARD Grade A", "NABARD Grade B", "LIC AAO", "LIC Assistant", "SIDBI", "EXIM Bank"],
    
    # 11. Railways
    ["RRB NTPC", "RRB Group D", "RRB JE", "RRB ALP", "RRB Paramedical", "RRB Ministerial"],
    
    # 12. Defence & Paramilitary
    ["Indian Army Agniveer", "Indian Army TES", "Indian Army TGC", "Indian Army SSC Tech", "Indian Navy Agniveer", "Indian Navy Cadet", "Indian Air Force Agniveer", "AFCAT", "Coast Guard", "Defence Civilian", "SSB", "Medical Entry (AFMC, MNS)"],
    
    # 13. State PSCs (All 28 States & UTs)
    ["TNPSC Group 1, 2, 4", "UPPSC PCS", "MPSC State Services", "BPSC CCE", "RPSC RAS", "WBPSC WBCS", "GPSC", "KPSC KAS", "MPPSC", "OPSC OCS", "HPPSC HAS", "UKPSC", "JK PSC", "APPSC", "TSPSC", "Kerala PSC", "Assam PSC"],
    
    # 14. State Departmental & TETs
    ["CTET", "State TETs (TNTET, UPTET, BTET, KTET, etc.)", "State Police SI", "State Police Constable", "State Forest Guard", "State Judicial Service (Civil Judge)", "State PSUs"],
    
    # 15. Private & Corporate Companies
    ["TCS NQT", "Infosys InfyTQ", "Wipro Elite NTH", "HCL TechBee", "Tech Mahindra", "Cognizant GenC", "Accenture", "Capgemini", "IBM", "LTIMindtree", "Deloitte", "EY", "KPMG", "PwC", "Amazon", "Microsoft", "Google", "Oracle", "SAP", "Adobe", "Cisco", "JPMorgan", "Goldman Sachs", "Morgan Stanley", "HSBC", "Barclays", "Citi", "American Express", "Mastercard", "Visa", "Walmart", "AMCAT", "CoCubes", "eLitmus", "Mettl"],
    
    # 16. Professional Certifications & Regulators
    ["CA Foundation", "CA Inter", "CA Final", "CS CSEET", "CS Executive", "CS Professional", "CMA", "Actuarial", "CFA", "FRM", "NISM Series", "IRDAI", "FSSAI FoSTaC", "GSTP", "PMP", "PRINCE2", "Scrum Master", "Six Sigma", "AWS", "Microsoft Azure", "Cisco CCNA", "Google Cloud", "RedHat", "USMLE", "PLAB", "NCLEX"],
    
    # 17. Online Learning & MOOCs
    ["SWAYAM", "SWAYAM Plus", "NPTEL", "UGC Online Learning", "AICTE Online Learning", "University MOOCs", "Government e-learning certifications"],
    
    # 18. Foreign Study & Immigration
    ["IELTS", "TOEFL", "PTE", "GRE", "GMAT", "SAT", "ACT", "Immigration Tests", "Foreign University Admissions", "Foreign Government Recruitment", "Foreign Professional Exams"]
]

def get_prompt(exam_batch):
    batch_str = ", ".join(exam_batch)
    return f"""
You are the Chief Exam Architect. 
Generate the exact exam pattern for these specific exams or categories: {batch_str}.
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
