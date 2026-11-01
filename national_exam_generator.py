import os, json, time, re
from dotenv import load_dotenv
from supabase import create_client
from openai import OpenAI
from google import genai
import json_repair

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

# AI Clients
GROQ_KEY = os.getenv("GROQ_API_KEY_1")
NVIDIA_KEY = os.getenv("NVIDIA_API_KEY_1")
GEMINI_KEY = os.getenv("GEMINI_API_KEY_1")

groq = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_KEY) if GROQ_KEY else None
nvidia = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=NVIDIA_KEY) if NVIDIA_KEY else None
gemini = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

def call_ai(prompt):
    # Groq is fastest for large JSON
    if groq:
        try:
            print(f"      🧠 Asking Groq...")
            resp = groq.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=8000, timeout=45
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ Groq failed: {str(e)[:80]}")

    if nvidia:
        try:
            print(f"      🧠 Asking NVIDIA...")
            resp = nvidia.chat.completions.create(
                model="nvidia/nemotron-3-super-120b-a12b",
                messages=[{"role": "system", "content": "Output ONLY valid JSON."}, {"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=8000, timeout=45
            )
            raw = re.sub(r'^```json\s*|\s*```$', '', resp.choices[0].message.content.strip(), flags=re.MULTILINE).strip()
            data = json_repair.loads(raw)
            if data and "exams" in data: return data["exams"]
        except Exception as e: print(f"      ⚠️ NVIDIA failed: {str(e)[:80]}")

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
print(f"✅ Loaded {len(valid_topics)} topics.")

# 🚨 THE NATIONAL TAXONOMY SWEEPS
# We ask the AI to find ALL exams in these massive categories at once.
national_categories = [
    {
        "category": "National School, Boards & Scholarships",
        "prompt_desc": "ALL national-level school exams, boards, and scholarships in India. Include CBSE Class 1-12, ICSE Class 1-12, NIOS, Navodaya (JNVST), Sainik School (AISSEE), NTSE, NMMS, and all major Olympiads (SOF, HBCSE). Map Class 1-5 to Level 1-3, Class 6-8 to Level 4-5, Class 9-12 to Level 6-7."
    },
    {
        "category": "National Higher Education Entrances (UG, PG, PhD)",
        "prompt_desc": "ALL national-level higher education entrances. Include UG (JEE Main, JEE Advanced, NEET-UG, CUET-UG, CLAT, NDA, BITSAT), PG (GATE, CAT, XAT, CUET-PG, NEET-PG), PhD (UGC-NET, CSIR-NET), and Foreign Study (IELTS, TOEFL, GRE, GMAT, USMLE, PLAB)."
    },
    {
        "category": "National Govt Jobs (Central & Defence)",
        "prompt_desc": "ALL central government and defence jobs. Include UPSC (CSE, CDS, CAPF, ESE), SSC (CGL, CHSL, MTS, GD, CPO, JE), Banking (IBPS PO, Clerk, SBI PO, Clerk, RBI Grade B), Railways (RRB NTPC, Group D, JE, ALP), and Defence (NDA, CDS, AFCAT)."
    },
    {
        "category": "National Professional, Skills & Corporate",
        "prompt_desc": "ALL professional, skill-based, and corporate exams. Include CA, CS, CMA, FSSAI, NISM, IRDAI, and IT corporate tests (TCS NQT, Infosys, Wipro, Accenture)."
    }
]

def get_prompt(category, prompt_desc):
    return f"""
You are the Chief Exam Architect for TryIT Educations.
Your task: Generate the complete exam registry for the category: "{category}".

CRITICAL INSTRUCTIONS:
1. Find ALL exams in this category: {prompt_desc}
2. For each exam, you MUST include all its Tiers/Stages (e.g., Tier 1, Tier 2, Prelims, Mains, Paper 1).
3. Map sections to our valid topics. Do NOT invent new topic_ids. Valid topics include: {valid_topics_str}, etc.
4. Negative marking must be a decimal (e.g., 0.25, 0.50, 0.333, or 0.0). Class 1-5 exams should have 0.0.
5. Output MUST be a valid JSON object with an "exams" array.

Format required:
{{
  "exams": [
    {{
      "exam_id": "unique_slug",
      "exam_name": "Exact Name",
      "conducting_body": "Body",
      "category": "{category}",
      "qualification_level": "10th/12th/graduate/etc",
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

for cat_data in national_categories:
    cat_name = cat_data["category"]
    print(f"\n🌍 Processing Category: {cat_name}")
    
    exams_data = call_ai(get_prompt(cat_name, cat_data["prompt_desc"]))
    
    if not exams_data:
        print(f"  ❌ Failed to generate data for {cat_name}.")
        continue
        
    print(f"  📥 Generated {len(exams_data)} exams. Pushing to DB...")
    
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
                    "negative_marking_rate": tier.get("negative_marking_rate"), "mode": "online_cbt"
                }).execute()
                
                for section in tier.get("sections", []):
                    section_id = section.get("section_id")
                    s.table('exam_sections').upsert({
                        "section_id": section_id, "tier_id": tier_id, "section_name": section.get("section_name"),
                        "num_questions": section.get("num_questions"), "marks_per_question": section.get("marks_per_question"),
                        "subject_group": section.get("subject_group")
                    }).execute()
                    
                    # 3. Map Topics
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
            
    time.sleep(3) 

print("\n🎉 NATIONAL TAXONOMY GENERATION COMPLETE!")
