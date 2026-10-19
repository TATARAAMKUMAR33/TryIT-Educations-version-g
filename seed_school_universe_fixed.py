import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("🚀 Fixing School Universe Seeding...")

# 1. THE MISSING SECTIONS (Must be added before mapping!)
school_sections = [
    # Sainik School Class 6 Sections
    {"section_id": "sainik_class6_paper1_maths", "tier_id": "sainik_class6_paper1", "section_name": "Mathematics", "subject_group": "quant", "num_questions": 50, "marks_per_question": 2.0},
    {"section_id": "sainik_class6_paper1_intelligence", "tier_id": "sainik_class6_paper1", "section_name": "Intelligence", "subject_group": "reasoning", "num_questions": 25, "marks_per_question": 2.0},
    
    # Navodaya Class 6 Sections
    {"section_id": "jnvst_class6_paper1_mat", "tier_id": "jnvst_class6_paper1", "section_name": "Mental Ability Test", "subject_group": "reasoning", "num_questions": 40, "marks_per_question": 1.0},
    {"section_id": "jnvst_class6_paper1_arith", "tier_id": "jnvst_class6_paper1", "section_name": "Arithmetic Test", "subject_group": "quant", "num_questions": 20, "marks_per_question": 1.0},
    
    # TN Board Class 10 Sections
    {"section_id": "tn_class10_paper1_maths", "tier_id": "tn_class10_paper1", "section_name": "Mathematics", "subject_group": "quant", "num_questions": 14, "marks_per_question": 1.0},
    {"section_id": "tn_class10_paper1_science", "tier_id": "tn_class10_paper1", "section_name": "Science", "subject_group": "science_gen", "num_questions": 14, "marks_per_question": 1.0}
]

print("📥 Seeding Missing Exam Sections...")
for section in school_sections:
    s.table('exam_sections').upsert(section).execute()
print("✅ Sections Created.")

# 2. MAP SECTIONS TO OUR TOPICS (The Matrix)
school_syllabus_map = [
    # Sainik School Class 6
    ("sainik_school_class6", "sainik_class6_paper1_maths", "maths_arithmetic_number_system", 20),
    ("sainik_school_class6", "sainik_class6_paper1_maths", "maths_arithmetic_average", 15),
    ("sainik_school_class6", "sainik_class6_paper1_intelligence", "reasoning_verbal_analogy", 25),
    
    # Navodaya Class 6
    ("jnvst_class6", "jnvst_class6_paper1_mat", "reasoning_nonverbal_figure_series", 30),
    ("jnvst_class6", "jnvst_class6_paper1_arith", "maths_arithmetic_percentage", 20),
    
    # Tamil Nadu Class 10
    ("tn_board_class10", "tn_class10_paper1_maths", "maths_algebra_linear_equations", 20),
    ("tn_board_class10", "tn_class10_paper1_science", "science_gen_everyday_science_applications", 15),
]

print("📥 Mapping Exam Sections to Topics...")
for exam_id, section_id, topic_id, weightage in school_syllabus_map:
    # Ensure topic exists in DB before linking
    topic_check = s.table('topics').select('topic_id').eq('topic_id', topic_id).execute()
    if not topic_check.data:
        print(f"  ⚠️ Topic '{topic_id}' not found. Skipping.")
        continue
    row = {
        "map_id": f"map_{exam_id}_{section_id}_{topic_id}",
        "exam_id": exam_id,
        "section_id": section_id,
        "topic_id": topic_id,
        "weightage_percent": weightage,
        "priority": 1 # High priority for school exams
    }
    s.table('exam_syllabus_map').upsert(row).execute()

print("🎉 School Universe Successfully Seeded!")
