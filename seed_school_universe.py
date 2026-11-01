import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=".env")
s = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

print("🚀 Seeding the Complete School Board & Exam Universe...")

# 1. THE BOARDS AND SPECIALIZED EXAMS
school_entities = [
    # Central Boards
    {"exam_id": "cbse_class10", "exam_name": "CBSE Class 10 Board", "conducting_body": "CBSE", "category": "k12_board", "qualification_level": "Class 10", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "cbse_class12", "exam_name": "CBSE Class 12 Board", "conducting_body": "CBSE", "category": "k12_board", "qualification_level": "Class 12", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "icse_class10", "exam_name": "ICSE Class 10 Board", "conducting_body": "CISCE", "category": "k12_board", "qualification_level": "Class 10", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "isc_class12", "exam_name": "ISC Class 12 Board", "conducting_body": "CISCE", "category": "k12_board", "qualification_level": "Class 12", "frequency_type": "annual", "research_status": "deep_dived"},
    
    # International Boards
    {"exam_id": "ib_dp", "exam_name": "IB Diploma Programme (DP)", "conducting_body": "IBO", "category": "k12_board", "qualification_level": "Class 11-12", "frequency_type": "annual", "research_status": "pass1_mapped_only"},
    {"exam_id": "cambridge_igcse", "exam_name": "Cambridge IGCSE / AS & A Level", "conducting_body": "CAIE", "category": "k12_board", "qualification_level": "Class 9-12", "frequency_type": "annual", "research_status": "pass1_mapped_only"},
    
    # State Boards (Specific Examples)
    {"exam_id": "tn_board_class10", "exam_name": "Tamil Nadu State Board Class 10", "conducting_body": "TN DGE", "category": "state_govt", "qualification_level": "Class 10", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "tn_board_class12", "exam_name": "Tamil Nadu State Board Class 12", "conducting_body": "TN DGE", "category": "state_govt", "qualification_level": "Class 12", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "msbshse_class10", "exam_name": "Maharashtra State Board Class 10", "conducting_body": "MSBSHSE", "category": "state_govt", "qualification_level": "Class 10", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "msbshse_class12", "exam_name": "Maharashtra State Board Class 12", "conducting_body": "MSBSHSE", "category": "state_govt", "qualification_level": "Class 12", "frequency_type": "annual", "research_status": "deep_dived"},
    
    # Specialized Entrance Exams
    {"exam_id": "sainik_school_class6", "exam_name": "Sainik School Entrance (AISSEE) Class 6", "conducting_body": "Sainik Schools Society", "category": "k12_entrance", "qualification_level": "Class 6", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "sainik_school_class9", "exam_name": "Sainik School Entrance (AISSEE) Class 9", "conducting_body": "Sainik Schools Society", "category": "k12_entrance", "qualification_level": "Class 9", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "jnvst_class6", "exam_name": "Navodaya Vidyalaya (JNVST) Class 6", "conducting_body": "NVS", "category": "k12_entrance", "qualification_level": "Class 6", "frequency_type": "annual", "research_status": "deep_dived"},
    {"exam_id": "jnvst_class9", "exam_name": "Navodaya Vidyalaya (JNVST) Class 9", "conducting_body": "NVS", "category": "k12_entrance", "qualification_level": "Class 9", "frequency_type": "annual", "research_status": "deep_dived"},
]

for entity in school_entities:
    s.table('exam_registry').upsert(entity).execute()
print(f"✅ {len(school_entities)} School Boards & Entrance Exams Registered.")

# 2. THE PATTERNS (Tiers)
# We are mapping the exact structure for a few key exams to prove the matrix works.
school_tiers = [
    # Sainik School Class 6 Pattern
    {"tier_id": "sainik_class6_paper1", "exam_id": "sainik_school_class6", "tier_name": "Single Paper", "is_qualifying": False, "total_questions": 125, "total_marks": 250, "duration_minutes": 150, "negative_marking_rate": 0.0, "mode": "offline_omr"},
    # Navodaya Class 6 Pattern
    {"tier_id": "jnvst_class6_paper1", "exam_id": "jnvst_class6", "tier_name": "Single Paper", "is_qualifying": False, "total_questions": 80, "total_marks": 100, "duration_minutes": 120, "negative_marking_rate": 0.0, "mode": "offline_omr"},
    # Tamil Nadu Class 10 Pattern (Example)
    {"tier_id": "tn_class10_paper1", "exam_id": "tn_board_class10", "tier_name": "Board Exam", "is_qualifying": False, "total_questions": 100, "total_marks": 100, "duration_minutes": 180, "negative_marking_rate": 0.0, "mode": "offline_omr"},
]

for tier in school_tiers:
    s.table('exam_tiers').upsert(tier).execute()
print("✅ School Exam Patterns (Tiers) Created.")

# 3. MAP SECTIONS TO OUR TOPICS (The Matrix)
# This is the crucial step: linking the board/exam to our specific topics.
school_syllabus_map = [
    # Sainik School Class 6 -> Maths and Intelligence
    ("sainik_school_class6", "sainik_class6_paper1", "maths_arithmetic_number_system", 20),
    ("sainik_school_class6", "sainik_class6_paper1", "maths_arithmetic_average", 15),
    ("sainik_school_class6", "sainik_class6_paper1", "reasoning_verbal_analogy", 25),
    
    # Navodaya Class 6 -> Mental Ability and Arithmetic
    ("jnvst_class6", "jnvst_class6_paper1", "reasoning_nonverbal_figure_series", 30),
    ("jnvst_class6", "jnvst_class6_paper1", "maths_arithmetic_percentage", 20),
    
    # Tamil Nadu Class 10 -> Core Subjects
    ("tn_board_class10", "tn_class10_paper1", "maths_algebra_linear_equations", 20),
    ("tn_board_class10", "tn_class10_paper1", "science_gen_everyday_science_applications", 15),
]

print("📥 Mapping Exam Sections to Topics...")
for exam_id, section_id, topic_id, weightage in school_syllabus_map:
    # Ensure topic exists
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
