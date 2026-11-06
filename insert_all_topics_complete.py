"""
TryIT Complete Lifetime Learning Universe - Phase 3 to 6
Every exam, course, language, skill from Class 1 to Retirement
India + International + Foreign Study + Return to India
~1500+ new topics
"""

import os, requests, json
from dotenv import load_dotenv

load_dotenv()
u = os.getenv('SUPABASE_URL')
k = os.getenv('SUPABASE_KEY')
h = {
    'apikey': k,
    'Authorization': f'Bearer {k}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=ignore-duplicates'
}

ALL_TOPICS = []

def add(topic_id, subject_id, topic_name, difficulty_range,
        is_visual=False, coverage_score=70, question_target=5000,
        launch_phase="phase_1_now", display_order=1):
    ALL_TOPICS.append({
        "topic_id": topic_id,
        "subject_id": subject_id,
        "topic_name": topic_name,
        "topic_name_hi": None,
        "topic_name_ta": None,
        "parent_topic_id": None,
        "difficulty_range": difficulty_range,
        "is_visual": is_visual,
        "coverage_score": coverage_score,
        "question_target": question_target,
        "questions_available": 0,
        "display_order": display_order,
        "launch_phase": launch_phase
    })

# ===========================================================================
# PHASE 3 — STATE BOARDS (All major Indian state boards chapter-wise)
# ===========================================================================

# Tamil Nadu State Board Class 6-12
for cls, lo, hi, score in [(6,1,3,80),(7,2,4,80),(8,3,5,82),(9,4,6,85),(10,5,7,88),(11,5,8,88),(12,6,9,90)]:
    add(f"tnboard_maths_class{cls}", "tn_state_board", f"TN Board Maths Class {cls}", f"{lo}-{hi}", False, score, 3000, "phase_1_now", cls)
    add(f"tnboard_science_class{cls}", "tn_state_board", f"TN Board Science Class {cls}", f"{lo}-{hi}", True, score, 3000, "phase_1_now", cls+20)
    add(f"tnboard_social_class{cls}", "tn_state_board", f"TN Board Social Science Class {cls}", f"{lo}-{hi}", False, score-5, 3000, "phase_1_now", cls+40)
    add(f"tnboard_english_class{cls}", "tn_state_board", f"TN Board English Class {cls}", f"{lo}-{hi}", False, score-5, 3000, "phase_1_now", cls+60)
    add(f"tnboard_tamil_class{cls}", "tn_state_board", f"TN Board Tamil Class {cls}", f"{lo}-{hi}", False, score, 3000, "phase_1_now", cls+80)

# Maharashtra State Board (SSC/HSC)
for cls, lo, hi, score in [(6,1,3,78),(7,2,4,78),(8,3,5,80),(9,4,6,83),(10,5,7,86),(11,5,8,86),(12,6,9,88)]:
    add(f"mhboard_maths_class{cls}", "mh_state_board", f"MH Board Maths Class {cls}", f"{lo}-{hi}", False, score, 3000, "phase_1_now", cls)
    add(f"mhboard_science_class{cls}", "mh_state_board", f"MH Board Science Class {cls}", f"{lo}-{hi}", True, score, 3000, "phase_1_now", cls+20)
    add(f"mhboard_history_class{cls}", "mh_state_board", f"MH Board History Class {cls}", f"{lo}-{hi}", False, score-5, 3000, "phase_1_now", cls+40)
    add(f"mhboard_marathi_class{cls}", "mh_state_board", f"MH Board Marathi Class {cls}", f"{lo}-{hi}", False, score, 3000, "phase_1_now", cls+60)

# Andhra Pradesh / Telangana State Board
for cls, lo, hi in [(6,1,3),(7,2,4),(8,3,5),(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"apboard_maths_class{cls}", "ap_ts_state_board", f"AP/TS Board Maths Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls)
    add(f"apboard_science_class{cls}", "ap_ts_state_board", f"AP/TS Board Science Class {cls}", f"{lo}-{hi}", True, 78, 3000, "phase_1_now", cls+20)
    add(f"apboard_telugu_class{cls}", "ap_ts_state_board", f"AP/TS Board Telugu Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls+40)
    add(f"apboard_social_class{cls}", "ap_ts_state_board", f"AP/TS Board Social Studies Class {cls}", f"{lo}-{hi}", False, 75, 3000, "phase_1_now", cls+60)

# Karnataka State Board
for cls, lo, hi in [(6,1,3),(7,2,4),(8,3,5),(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"kboard_maths_class{cls}", "karnataka_state_board", f"Karnataka Board Maths Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls)
    add(f"kboard_science_class{cls}", "karnataka_state_board", f"Karnataka Board Science Class {cls}", f"{lo}-{hi}", True, 78, 3000, "phase_1_now", cls+20)
    add(f"kboard_kannada_class{cls}", "karnataka_state_board", f"Karnataka Board Kannada Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls+40)

# UP Board (Uttar Pradesh)
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"upboard_maths_class{cls}", "up_state_board", f"UP Board Maths Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls)
    add(f"upboard_science_class{cls}", "up_state_board", f"UP Board Science Class {cls}", f"{lo}-{hi}", True, 80, 3000, "phase_1_now", cls+20)
    add(f"upboard_hindi_class{cls}", "up_state_board", f"UP Board Hindi Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls+40)
    add(f"upboard_english_class{cls}", "up_state_board", f"UP Board English Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls+60)

# Bihar Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"biharboard_maths_class{cls}", "bihar_state_board", f"Bihar Board Maths Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls)
    add(f"biharboard_science_class{cls}", "bihar_state_board", f"Bihar Board Science Class {cls}", f"{lo}-{hi}", True, 78, 3000, "phase_1_now", cls+20)

# ICSE Board Class 6-12
for cls, lo, hi, score in [(6,1,3,82),(7,2,4,82),(8,3,5,84),(9,4,6,86),(10,5,8,90),(11,5,8,88),(12,6,9,90)]:
    add(f"icse_maths_class{cls}", "icse_board", f"ICSE Maths Class {cls}", f"{lo}-{hi}", False, score, 3000, "phase_1_now", cls)
    add(f"icse_physics_class{cls}", "icse_board", f"ICSE Physics Class {cls}", f"{lo}-{hi}", True, score, 3000, "phase_1_now", cls+20)
    add(f"icse_chemistry_class{cls}", "icse_board", f"ICSE Chemistry Class {cls}", f"{lo}-{hi}", True, score, 3000, "phase_1_now", cls+40)
    add(f"icse_biology_class{cls}", "icse_board", f"ICSE Biology Class {cls}", f"{lo}-{hi}", True, score, 3000, "phase_1_now", cls+60)
    add(f"icse_english_class{cls}", "icse_board", f"ICSE English Language Class {cls}", f"{lo}-{hi}", False, score-3, 3000, "phase_1_now", cls+80)
    add(f"icse_history_class{cls}", "icse_board", f"ICSE History and Civics Class {cls}", f"{lo}-{hi}", False, score-5, 3000, "phase_1_now", cls+100)
    add(f"icse_geography_class{cls}", "icse_board", f"ICSE Geography Class {cls}", f"{lo}-{hi}", True, score-5, 3000, "phase_1_now", cls+120)

# Kerala Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"krlboard_maths_class{cls}", "kerala_state_board", f"Kerala Board Maths Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls)
    add(f"krlboard_science_class{cls}", "kerala_state_board", f"Kerala Board Science Class {cls}", f"{lo}-{hi}", True, 78, 3000, "phase_1_now", cls+20)
    add(f"krlboard_malayalam_class{cls}", "kerala_state_board", f"Kerala Board Malayalam Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls+40)

# Rajasthan Board (RBSE)
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"rbse_maths_class{cls}", "rajasthan_state_board", f"RBSE Maths Class {cls}", f"{lo}-{hi}", False, 76, 3000, "phase_1_now", cls)
    add(f"rbse_science_class{cls}", "rajasthan_state_board", f"RBSE Science Class {cls}", f"{lo}-{hi}", True, 76, 3000, "phase_1_now", cls+20)

# MP Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"mpboard_maths_class{cls}", "mp_state_board", f"MP Board Maths Class {cls}", f"{lo}-{hi}", False, 76, 3000, "phase_1_now", cls)
    add(f"mpboard_science_class{cls}", "mp_state_board", f"MP Board Science Class {cls}", f"{lo}-{hi}", True, 76, 3000, "phase_1_now", cls+20)

# West Bengal Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"wbboard_maths_class{cls}", "wb_state_board", f"WB Board Maths Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls)
    add(f"wbboard_science_class{cls}", "wb_state_board", f"WB Board Science Class {cls}", f"{lo}-{hi}", True, 78, 3000, "phase_1_now", cls+20)
    add(f"wbboard_bengali_class{cls}", "wb_state_board", f"WB Board Bengali Class {cls}", f"{lo}-{hi}", False, 80, 3000, "phase_1_now", cls+40)

# Gujarat Board (GSEB)
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"gseb_maths_class{cls}", "gujarat_state_board", f"GSEB Maths Class {cls}", f"{lo}-{hi}", False, 76, 3000, "phase_1_now", cls)
    add(f"gseb_science_class{cls}", "gujarat_state_board", f"GSEB Science Class {cls}", f"{lo}-{hi}", True, 76, 3000, "phase_1_now", cls+20)
    add(f"gseb_gujarati_class{cls}", "gujarat_state_board", f"GSEB Gujarati Class {cls}", f"{lo}-{hi}", False, 78, 3000, "phase_1_now", cls+40)

# Punjab Board (PSEB)
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"pseb_maths_class{cls}", "punjab_state_board", f"PSEB Maths Class {cls}", f"{lo}-{hi}", False, 74, 3000, "phase_1_now", cls)
    add(f"pseb_punjabi_class{cls}", "punjab_state_board", f"PSEB Punjabi Class {cls}", f"{lo}-{hi}", False, 76, 3000, "phase_1_now", cls+20)

# Odisha Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"odisha_maths_class{cls}", "odisha_state_board", f"Odisha Board Maths Class {cls}", f"{lo}-{hi}", False, 74, 3000, "phase_1_now", cls)
    add(f"odisha_odia_class{cls}", "odisha_state_board", f"Odisha Board Odia Class {cls}", f"{lo}-{hi}", False, 76, 3000, "phase_1_now", cls+20)

# Assam Board
for cls, lo, hi in [(9,4,6),(10,5,7),(11,5,8),(12,6,9)]:
    add(f"assam_maths_class{cls}", "assam_state_board", f"Assam Board Maths Class {cls}", f"{lo}-{hi}", False, 72, 3000, "phase_1_now", cls)
    add(f"assam_assamese_class{cls}", "assam_state_board", f"Assam Board Assamese Class {cls}", f"{lo}-{hi}", False, 74, 3000, "phase_1_now", cls+20)

# ===========================================================================
# ALL INDIAN LANGUAGES — Complete
# ===========================================================================

# Tamil — Full Course
add("tamil_grammar_sandhi", "tamil_full", "Tamil Sandhi and Grammar Rules (சந்தி)", "2-6", False, 88, 5000, "phase_1_now", 1)
add("tamil_poetry_ancient", "tamil_full", "Tamil Ancient Poetry (சங்க இலக்கியம்)", "5-9", False, 85, 5000, "phase_1_now", 2)
add("tamil_thirukkural", "tamil_full", "Thirukkural — All 133 Chapters", "3-8", False, 90, 5000, "phase_1_now", 3)
add("tamil_modern_literature", "tamil_full", "Tamil Modern Literature", "4-8", False, 82, 5000, "phase_1_now", 4)
add("tamil_writing_skills", "tamil_full", "Tamil Essay and Letter Writing", "3-7", False, 85, 5000, "phase_1_now", 5)
add("tamil_translation", "tamil_full", "Tamil-English Translation Skills", "4-7", False, 82, 5000, "phase_1_now", 6)
add("tamil_class6_12_all", "tamil_full", "Tamil Language Class 6-12 Complete", "1-8", False, 88, 5000, "phase_1_now", 7)
add("tamil_competitive_all", "tamil_full", "Tamil for All Competitive Exams", "4-9", False, 90, 5000, "phase_1_now", 8)

# Telugu — Full Course
add("telugu_grammar_full", "telugu_full", "Telugu Grammar (వ్యాకరణం) Complete", "2-6", False, 85, 5000, "phase_1_now", 1)
add("telugu_literature", "telugu_full", "Telugu Literature and Poetry", "4-8", False, 82, 5000, "phase_1_now", 2)
add("telugu_writing", "telugu_full", "Telugu Writing and Essay Skills", "3-7", False, 80, 5000, "phase_1_now", 3)
add("telugu_class6_12", "telugu_full", "Telugu Language Class 6-12", "1-8", False, 85, 5000, "phase_1_now", 4)
add("telugu_competitive", "telugu_full", "Telugu for APPSC/TSPSC Exams", "4-9", False, 88, 5000, "phase_1_now", 5)

# Kannada — Full Course
add("kannada_grammar_full", "kannada_full", "Kannada Grammar (ಕನ್ನಡ ವ್ಯಾಕರಣ) Complete", "2-6", False, 83, 5000, "phase_1_now", 1)
add("kannada_literature", "kannada_full", "Kannada Literature and Vachanas", "4-8", False, 80, 5000, "phase_1_now", 2)
add("kannada_class6_12", "kannada_full", "Kannada Language Class 6-12", "1-8", False, 83, 5000, "phase_1_now", 3)
add("kannada_competitive", "kannada_full", "Kannada for KPSC Exams", "4-9", False, 85, 5000, "phase_1_now", 4)

# Malayalam — Full Course
add("malayalam_grammar_full", "malayalam_full", "Malayalam Grammar (മലയാള വ്യാകരണം)", "2-6", False, 83, 5000, "phase_1_now", 1)
add("malayalam_literature", "malayalam_full", "Malayalam Literature and Poetry", "4-8", False, 80, 5000, "phase_1_now", 2)
add("malayalam_class6_12", "malayalam_full", "Malayalam Language Class 6-12", "1-8", False, 83, 5000, "phase_1_now", 3)
add("malayalam_competitive", "malayalam_full", "Malayalam for Kerala PSC Exams", "4-9", False, 85, 5000, "phase_1_now", 4)

# Marathi — Full Course
add("marathi_grammar_full", "marathi_full", "Marathi Grammar (मराठी व्याकरण) Complete", "2-6", False, 82, 5000, "phase_1_now", 1)
add("marathi_literature", "marathi_full", "Marathi Literature and Saints Poetry", "4-8", False, 80, 5000, "phase_1_now", 2)
add("marathi_class6_12", "marathi_full", "Marathi Language Class 6-12", "1-8", False, 82, 5000, "phase_1_now", 3)
add("marathi_competitive", "marathi_full", "Marathi for MPSC Exams", "4-9", False, 85, 5000, "phase_1_now", 4)

# Bengali — Full Course
add("bengali_grammar_full", "bengali_full", "Bengali Grammar (বাংলা ব্যাকরণ) Complete", "2-6", False, 82, 5000, "phase_1_now", 1)
add("bengali_literature", "bengali_full", "Bengali Literature: Tagore and Beyond", "4-8", False, 80, 5000, "phase_1_now", 2)
add("bengali_class6_12", "bengali_full", "Bengali Language Class 6-12", "1-8", False, 82, 5000, "phase_1_now", 3)
add("bengali_competitive", "bengali_full", "Bengali for WBCS Exams", "4-9", False, 83, 5000, "phase_1_now", 4)

# Gujarati — Full Course
add("gujarati_grammar_full", "gujarati_full", "Gujarati Grammar (ગુજરાતી વ્યાકરણ)", "2-6", False, 80, 5000, "phase_1_now", 1)
add("gujarati_literature", "gujarati_full", "Gujarati Literature and Poetry", "4-8", False, 78, 5000, "phase_1_now", 2)
add("gujarati_class6_12", "gujarati_full", "Gujarati Language Class 6-12", "1-8", False, 80, 5000, "phase_1_now", 3)
add("gujarati_competitive", "gujarati_full", "Gujarati for GPSC Exams", "4-9", False, 82, 5000, "phase_1_now", 4)

# Punjabi — Full Course
add("punjabi_grammar_full", "punjabi_full", "Punjabi Grammar (ਪੰਜਾਬੀ ਵਿਆਕਰਣ)", "2-6", False, 78, 5000, "phase_1_now", 1)
add("punjabi_literature", "punjabi_full", "Punjabi Literature and Gurbani", "4-8", False, 78, 5000, "phase_1_now", 2)
add("punjabi_class6_12", "punjabi_full", "Punjabi Language Class 6-12", "1-8", False, 78, 5000, "phase_1_now", 3)
add("punjabi_competitive", "punjabi_full", "Punjabi for PPSC Exams", "4-9", False, 80, 5000, "phase_1_now", 4)

# Odia — Full Course
add("odia_grammar_full", "odia_full", "Odia Grammar (ଓଡ଼ିଆ ବ୍ୟାକରଣ)", "2-6", False, 76, 5000, "phase_1_now", 1)
add("odia_literature", "odia_full", "Odia Literature and Classical Poetry", "4-8", False, 74, 5000, "phase_1_now", 2)
add("odia_class6_12", "odia_full", "Odia Language Class 6-12", "1-8", False, 76, 5000, "phase_1_now", 3)
add("odia_competitive", "odia_full", "Odia for OPSC Exams", "4-9", False, 78, 5000, "phase_1_now", 4)

# Assamese — Full Course
add("assamese_grammar_full", "assamese_full", "Assamese Grammar (অসমীয়া ব্যাকৰণ)", "2-6", False, 74, 5000, "phase_1_now", 1)
add("assamese_literature", "assamese_full", "Assamese Literature", "4-8", False, 72, 5000, "phase_1_now", 2)
add("assamese_competitive", "assamese_full", "Assamese for APSC Exams", "4-9", False, 76, 5000, "phase_1_now", 3)

# Sanskrit
add("sanskrit_grammar_basic", "sanskrit_full", "Sanskrit Grammar Basics (संस्कृत व्याकरण)", "3-7", False, 80, 5000, "phase_1_now", 1)
add("sanskrit_shlokas", "sanskrit_full", "Sanskrit Shlokas and Literature", "4-8", False, 78, 5000, "phase_1_now", 2)
add("sanskrit_class6_12", "sanskrit_full", "Sanskrit Language Class 6-12", "1-8", False, 80, 5000, "phase_1_now", 3)
add("sanskrit_competitive", "sanskrit_full", "Sanskrit for Competitive Exams", "4-9", False, 78, 5000, "phase_1_now", 4)

# Urdu
add("urdu_grammar_full", "urdu_full", "Urdu Grammar (اردو قواعد) Complete", "2-6", False, 76, 5000, "phase_1_now", 1)
add("urdu_literature", "urdu_full", "Urdu Literature, Ghazals and Poetry", "4-8", False, 74, 5000, "phase_1_now", 2)
add("urdu_class6_12", "urdu_full", "Urdu Language Class 6-12", "1-8", False, 76, 5000, "phase_1_now", 3)
add("urdu_competitive", "urdu_full", "Urdu for Competitive Exams", "4-9", False, 76, 5000, "phase_1_now", 4)

# Sindhi, Kashmiri, Dogri, Konkani, Bodo, Santali, Maithili, Manipuri, Nepali
for lang, code, score in [
    ("Sindhi","sindhi",70), ("Kashmiri","kashmiri",68), ("Dogri","dogri",66),
    ("Konkani","konkani",68), ("Bodo","bodo",66), ("Santali","santali",65),
    ("Maithili","maithili",68), ("Manipuri","manipuri",66), ("Nepali","nepali",70),
    ("Mizo","mizo",65), ("Khasi","khasi",65), ("Garo","garo",64), ("Tulu","tulu",65),
    ("Bhili","bhili",62), ("Gondi","gondi",62), ("Kokborok","kokborok",62)
]:
    add(f"{code}_grammar_basics", f"{code}_language", f"{lang} Grammar Basics", "2-6", False, score, 3000, "phase_1_now", 1)
    add(f"{code}_class_exam_prep", f"{code}_language", f"{lang} for Competitive Exams", "4-8", False, score+2, 3000, "phase_1_now", 2)

# ===========================================================================
# FOREIGN LANGUAGES — All levels
# ===========================================================================

# French — Complete A1 to C2
for level, lo, hi, score in [("A1",1,3,80),("A2",2,4,78),("B1",4,6,78),("B2",5,7,76),("C1",6,8,74),("C2",7,9,72)]:
    add(f"french_{level.lower()}_complete", "french_language", f"French {level} Level Complete", f"{lo}-{hi}", False, score, 5000, "phase_1_now", ord(level[0])-64)
add("french_delf_b2_exam", "french_language", "DELF B2 Exam Preparation", "5-8", False, 78, 5000, "phase_1_now", 10)
add("french_dalf_c1_exam", "french_language", "DALF C1 Exam Preparation", "6-9", False, 75, 5000, "phase_2_2027", 11)
add("french_business", "french_language", "Business French for Professionals", "5-8", False, 78, 5000, "phase_1_now", 12)

# German — Complete A1 to C2
for level, lo, hi, score in [("A1",1,3,78),("A2",2,4,76),("B1",4,6,76),("B2",5,7,74),("C1",6,8,72),("C2",7,9,70)]:
    add(f"german_{level.lower()}_complete", "german_language", f"German {level} Level Complete", f"{lo}-{hi}", False, score, 5000, "phase_1_now", ord(level[0])-64)
add("german_goethe_b2", "german_language", "Goethe-Zertifikat B2 Exam Prep", "5-8", False, 75, 5000, "phase_1_now", 10)
add("german_testdaf", "german_language", "TestDaF Exam Preparation (University Entry)", "6-9", False, 72, 5000, "phase_2_2027", 11)
add("german_business", "german_language", "Business German for Professionals", "5-8", False, 74, 5000, "phase_1_now", 12)

# Spanish — Complete A1 to C2
for level, lo, hi, score in [("A1",1,3,78),("A2",2,4,76),("B1",4,6,76),("B2",5,7,74),("C1",6,8,72)]:
    add(f"spanish_{level.lower()}_complete", "spanish_language", f"Spanish {level} Level Complete", f"{lo}-{hi}", False, score, 5000, "phase_1_now", ord(level[0])-64)
add("spanish_dele_b2", "spanish_language", "DELE B2 Exam Preparation", "5-8", False, 74, 5000, "phase_1_now", 10)
add("spanish_latin_america", "spanish_language", "Latin American Spanish Varieties", "4-7", False, 70, 5000, "phase_2_2027", 11)

# Japanese — Complete N5 to N1
for level, lo, hi, score in [("N5",2,4,76),("N4",3,5,74),("N3",4,6,74),("N2",5,7,72),("N1",6,9,70)]:
    add(f"japanese_{level.lower()}_complete", "japanese_language", f"Japanese JLPT {level} Complete", f"{lo}-{hi}", False, score, 5000, "phase_1_now", int(level[1]))
add("japanese_business", "japanese_language", "Business Japanese for IT Professionals", "5-8", False, 72, 5000, "phase_1_now", 10)
add("japanese_kanji_practice", "japanese_language", "Japanese Kanji Writing Practice", "3-8", False, 72, 5000, "phase_1_now", 11)

# Mandarin Chinese — HSK 1 to 6
for level in range(1,7):
    lo = max(1, level*1)
    hi = min(9, level+2)
    add(f"mandarin_hsk{level}", "mandarin_chinese", f"Mandarin Chinese HSK {level}", f"{lo}-{hi}", False, 78-level, 5000, "phase_1_now", level)
add("mandarin_business", "mandarin_chinese", "Business Mandarin for Trade with China", "5-8", False, 74, 5000, "phase_1_now", 10)
add("mandarin_hsk_writing", "mandarin_chinese", "Mandarin Character Writing Practice", "3-8", False, 72, 5000, "phase_2_2027", 11)

# Korean — TOPIK I and II
for level, lo, hi, score in [("Beginner",1,3,74),("Elementary",2,4,72),("Intermediate",4,6,72),("Advanced",6,8,70)]:
    add(f"korean_{level.lower()}", "korean_language", f"Korean Language {level}", f"{lo}-{hi}", False, score, 5000, "phase_1_now", 1)
add("korean_topik1", "korean_language", "TOPIK I Exam Preparation", "2-5", False, 72, 5000, "phase_1_now", 5)
add("korean_topik2", "korean_language", "TOPIK II Exam Preparation", "5-8", False, 70, 5000, "phase_2_2027", 6)
add("korean_kpop_culture", "korean_language", "Korean through K-pop and K-drama Culture", "1-4", False, 76, 3000, "phase_1_now", 7)

# Arabic
add("arabic_a1_a2", "arabic_language", "Arabic Language A1-A2 (Modern Standard)", "2-5", False, 74, 5000, "phase_1_now", 1)
add("arabic_b1_b2", "arabic_language", "Arabic Language B1-B2", "4-7", False, 72, 5000, "phase_1_now", 2)
add("arabic_quran_reading", "arabic_language", "Quranic Arabic Reading and Understanding", "3-7", False, 76, 5000, "phase_1_now", 3)
add("arabic_gulf_dialect", "arabic_language", "Gulf Arabic for Working in GCC Countries", "4-7", False, 74, 5000, "phase_1_now", 4)

# Portuguese
add("portuguese_a1_b2", "portuguese_language", "Portuguese A1-B2 (European and Brazilian)", "2-7", False, 70, 5000, "phase_1_now", 1)
add("portuguese_celpe_bras", "portuguese_language", "Celpe-Bras Exam for Brazil Study/Work", "5-8", False, 68, 5000, "phase_2_2027", 2)

# Italian
add("italian_a1_b2", "italian_language", "Italian A1-B2 Complete", "2-7", False, 70, 5000, "phase_1_now", 1)
add("italian_cils_exam", "italian_language", "CILS Italian Certification Exam Prep", "5-8", False, 68, 5000, "phase_2_2027", 2)

# Russian
add("russian_a1_b1", "russian_language", "Russian A1-B1 Complete", "3-7", False, 68, 5000, "phase_2_2027", 1)
add("russian_torfl", "russian_language", "TORFL Russian Language Certification", "5-8", False, 65, 5000, "phase_2_2027", 2)

# Dutch, Swedish, Norwegian, Danish (for EU/Nordic jobs)
for lang, code in [("Dutch","dutch"),("Swedish","swedish"),("Norwegian","norwegian"),("Danish","danish")]:
    add(f"{code}_a1_b1", f"{code}_language", f"{lang} A1-B1 for Work in Europe", "2-6", False, 65, 3000, "phase_2_2027", 1)

# ===========================================================================
# GOING ABROAD — Every pathway
# ===========================================================================

# Study in USA
add("usa_f1_visa_process", "study_abroad_usa", "USA F1 Student Visa Process and Interview", "3-6", False, 88, 5000, "phase_1_now", 1)
add("usa_university_admissions", "study_abroad_usa", "US University Admissions (Common App, Essays)", "4-7", False, 85, 5000, "phase_1_now", 2)
add("usa_stem_programs", "study_abroad_usa", "STEM Programs and OPT/CPT in USA", "4-7", False, 85, 5000, "phase_1_now", 3)
add("usa_gre_complete", "study_abroad_usa", "Complete GRE Preparation (Verbal+Quant+AWA)", "5-9", False, 90, 5000, "phase_1_now", 4)
add("usa_gmat_complete", "study_abroad_usa", "Complete GMAT Preparation", "5-9", False, 88, 5000, "phase_1_now", 5)
add("usa_sat_act_complete", "study_abroad_usa", "SAT and ACT Complete Preparation", "4-8", False, 82, 5000, "phase_1_now", 6)
add("usa_scholarship_guide", "study_abroad_usa", "US Scholarships: Fulbright, Chevening, Others", "3-6", False, 82, 5000, "phase_1_now", 7)
add("usa_life_work_culture", "study_abroad_usa", "Living and Working in USA — Indian Student Guide", "2-5", False, 80, 5000, "phase_1_now", 8)

# Study in UK
add("uk_tier4_visa", "study_abroad_uk", "UK Student Visa (Tier 4) Process", "3-6", False, 85, 5000, "phase_1_now", 1)
add("uk_university_admissions", "study_abroad_uk", "UCAS and UK University Admissions Guide", "4-7", False, 82, 5000, "phase_1_now", 2)
add("uk_ielts_ukvi", "study_abroad_uk", "IELTS UKVI for UK Study and Work Visa", "4-8", False, 88, 5000, "phase_1_now", 3)
add("uk_scholarships", "study_abroad_uk", "UK Scholarships: Chevening, Commonwealth, Rhodes", "4-7", False, 82, 5000, "phase_1_now", 4)
add("uk_graduate_visa", "study_abroad_uk", "UK Graduate Route Visa and Work Rights", "3-6", False, 80, 5000, "phase_1_now", 5)
add("uk_plab_exam", "study_abroad_uk", "PLAB Exam for Doctors in UK (Part 1 and 2)", "7-10", False, 78, 5000, "phase_1_now", 6)
add("uk_nmc_nursing", "study_abroad_uk", "UK NMC Registration for Indian Nurses", "5-8", False, 76, 5000, "phase_1_now", 7)

# Study in Canada
add("canada_study_permit", "study_abroad_canada", "Canada Study Permit and SDS Program", "3-6", False, 85, 5000, "phase_1_now", 1)
add("canada_university_admissions", "study_abroad_canada", "Canadian University Admissions Guide", "4-7", False, 82, 5000, "phase_1_now", 2)
add("canada_pgwp_pr", "study_abroad_canada", "Canada PGWP and Permanent Residency Path", "4-7", False, 85, 5000, "phase_1_now", 3)
add("canada_celpip_exam", "study_abroad_canada", "CELPIP English Test for Canada PR", "4-8", False, 82, 5000, "phase_1_now", 4)
add("canada_express_entry", "study_abroad_canada", "Canada Express Entry and CRS Score Guide", "3-7", False, 85, 5000, "phase_1_now", 5)
add("canada_pnp_programs", "study_abroad_canada", "Canada Provincial Nominee Programs (PNP)", "4-7", False, 80, 5000, "phase_1_now", 6)
add("canada_french_advantage", "study_abroad_canada", "French Advantage for Canada PR (CLB)", "4-7", False, 78, 5000, "phase_1_now", 7)

# Study in Australia
add("australia_student_visa", "study_abroad_australia", "Australia Student Visa (Subclass 500)", "3-6", False, 83, 5000, "phase_1_now", 1)
add("australia_university_tafe", "study_abroad_australia", "Australian Universities and TAFE Admissions", "3-7", False, 80, 5000, "phase_1_now", 2)
add("australia_pr_pathway", "study_abroad_australia", "Australia PR Pathway for Indian Students", "4-7", False, 83, 5000, "phase_1_now", 3)
add("australia_pte_exam", "study_abroad_australia", "PTE Academic Exam Preparation", "4-8", False, 85, 5000, "phase_1_now", 4)
add("australia_skilled_migration", "study_abroad_australia", "Australia Skilled Migration and 189/190 Visa", "4-7", False, 80, 5000, "phase_1_now", 5)
add("australia_mcat_amc", "study_abroad_australia", "AMC Exam for Indian Doctors in Australia", "7-10", False, 74, 5000, "phase_2_2027", 6)

# Study in Germany
add("germany_student_visa", "study_abroad_germany", "Germany Student Visa and Blocked Account", "3-6", False, 82, 5000, "phase_1_now", 1)
add("germany_uni_admissions", "study_abroad_germany", "German University Admissions (Uni-Assist)", "4-7", False, 80, 5000, "phase_1_now", 2)
add("germany_job_seeker_visa", "study_abroad_germany", "Germany Job Seeker Visa for Indian Graduates", "3-7", False, 82, 5000, "phase_1_now", 3)
add("germany_blue_card", "study_abroad_germany", "Germany EU Blue Card for Skilled Workers", "4-7", False, 80, 5000, "phase_1_now", 4)
add("germany_testdaf_complete", "study_abroad_germany", "TestDaF and DSH German Proficiency Exams", "5-9", False, 76, 5000, "phase_1_now", 5)

# Study in Other Countries
add("singapore_study_work", "study_abroad_other", "Singapore Study and Employment Pass Guide", "3-7", False, 80, 5000, "phase_1_now", 1)
add("uae_work_visa_guide", "study_abroad_other", "UAE Work Visa and Golden Visa for Indians", "3-7", False, 82, 5000, "phase_1_now", 2)
add("new_zealand_study", "study_abroad_other", "New Zealand Study and Work Visa Guide", "3-7", False, 76, 5000, "phase_1_now", 3)
add("ireland_study_visa", "study_abroad_other", "Ireland Study and Stamp 1G Work Rights", "3-7", False, 76, 5000, "phase_1_now", 4)
add("schengen_visa_europe", "study_abroad_other", "Schengen Visa for Study/Work in Europe", "2-6", False, 80, 5000, "phase_1_now", 5)
add("japan_work_visa_it", "study_abroad_other", "Japan Work Visa for IT Professionals (HSP)", "4-8", False, 74, 5000, "phase_1_now", 6)
add("south_korea_d2_d10", "study_abroad_other", "South Korea D-2 Student and D-10 Job Visa", "3-7", False, 72, 5000, "phase_2_2027", 7)
add("netherlands_highly_skilled", "study_abroad_other", "Netherlands Highly Skilled Migrant Visa", "4-7", False, 72, 5000, "phase_2_2027", 8)
add("sweden_self_employment", "study_abroad_other", "Sweden and Nordic Countries Work Visa", "3-7", False, 68, 5000, "phase_2_2027", 9)
add("gulf_gcc_work_guide", "study_abroad_other", "Gulf Countries Work Visa Guide (Saudi, Qatar, Kuwait, Bahrain)", "2-6", False, 82, 5000, "phase_1_now", 10)

# ===========================================================================
# RETURNING TO INDIA — Re-entry exams and recognition
# ===========================================================================
add("foreign_degree_recognition", "return_india", "Foreign Degree Recognition in India (AIU)", "3-6", False, 78, 5000, "phase_1_now", 1)
add("nri_upsc_eligibility", "return_india", "NRI and OCI Card Holders UPSC Eligibility", "3-6", False, 76, 5000, "phase_1_now", 2)
add("foreign_doctor_india", "return_india", "Foreign Medical Graduates Exam (FMGE/NExT)", "7-10", False, 82, 5000, "phase_1_now", 3)
add("foreign_nurse_india", "return_india", "Foreign Qualified Nurses Returning to India", "4-7", False, 74, 5000, "phase_1_now", 4)
add("lateral_entry_psu", "return_india", "PSU Lateral Entry for Experienced Returnees", "5-8", False, 76, 5000, "phase_1_now", 5)
add("startup_india_returnee", "return_india", "Startup India and DPIIT Registration for Returnees", "3-7", False, 76, 5000, "phase_1_now", 6)
add("nri_investment_taxes", "return_india", "NRI Investment and Tax Rules on Return to India", "4-8", False, 78, 5000, "phase_1_now", 7)
add("make_in_india_opportunities", "return_india", "Make in India Opportunities for Returning NRIs", "3-6", False, 72, 5000, "phase_1_now", 8)

# ===========================================================================
# PROFESSIONAL MEDICAL — Complete
# ===========================================================================
add("neet_pg_psychiatry", "medical_pg", "NEET PG Psychiatry", "7-10", False, 80, 5000, "phase_1_now", 5)
add("neet_pg_pediatrics", "medical_pg", "NEET PG Pediatrics", "7-10", False, 80, 5000, "phase_1_now", 6)
add("neet_pg_obgyn", "medical_pg", "NEET PG Obstetrics and Gynecology", "7-10", False, 80, 5000, "phase_1_now", 7)
add("neet_pg_radiology", "medical_pg", "NEET PG Radiology and Imaging", "7-10", False, 78, 5000, "phase_1_now", 8)
add("neet_pg_ortho", "medical_pg", "NEET PG Orthopedics", "7-10", False, 78, 5000, "phase_1_now", 9)
add("next_exam_india", "medical_pg", "NExT Exam (National Exit Test for MBBS)", "7-10", False, 85, 5000, "phase_1_now", 10)
add("norcet_nursing_aiims", "medical_pg", "NORCET Nursing Exam for AIIMS", "5-9", False, 82, 5000, "phase_1_now", 11)
add("usmle_step2_ck", "usmle_prep", "USMLE Step 2 CK Clinical Knowledge", "7-10", False, 80, 5000, "phase_1_now", 4)
add("usmle_step3", "usmle_prep", "USMLE Step 3 (Residency Entry)", "7-10", False, 78, 5000, "phase_2_2027", 5)
add("mrcpuk_part1", "international_medical", "MRCP UK Part 1 (Royal College Physicians)", "7-10", False, 76, 5000, "phase_1_now", 1)
add("mrcs_surgery", "international_medical", "MRCS Surgery (Royal College of Surgeons)", "7-10", False, 74, 5000, "phase_1_now", 2)
add("plab1_exam", "international_medical", "PLAB 1 Exam for UK Medical Registration", "7-10", False, 78, 5000, "phase_1_now", 3)
add("amc_part1_australia", "international_medical", "AMC Part 1 MCQ for Australia Medical", "7-10", False, 74, 5000, "phase_2_2027", 4)
add("mccqe_canada_medical", "international_medical", "MCCQE for Canadian Medical Licensure", "7-10", False, 72, 5000, "phase_2_2027", 5)
add("pharmacy_gpat_exam", "pharmacy", "GPAT Pharmacy Entrance Exam", "5-9", False, 82, 5000, "phase_1_now", 1)
add("pharmacy_dpharm_bpharm", "pharmacy", "D.Pharm and B.Pharm Complete Syllabus", "4-8", False, 80, 5000, "phase_1_now", 2)
add("pharmacy_drug_regulations", "pharmacy", "Indian Pharmacy Drug Laws and Regulations", "5-8", False, 78, 5000, "phase_1_now", 3)

# ===========================================================================
# ENGINEERING — All branches
# ===========================================================================
add("gate_mechanical_full", "gate_prep", "GATE Mechanical Engineering Complete", "6-10", False, 90, 5000, "phase_1_now", 1)
add("gate_civil_full", "gate_prep", "GATE Civil Engineering Complete", "6-10", False, 88, 5000, "phase_1_now", 2)
add("gate_electrical_full", "gate_prep", "GATE Electrical Engineering Complete", "6-10", False, 88, 5000, "phase_1_now", 3)
add("gate_electronics_full", "gate_prep", "GATE Electronics and Communication (ECE) Complete", "6-10", False, 88, 5000, "phase_1_now", 4)
add("gate_cs_full", "gate_prep", "GATE Computer Science (CS/IT) Complete", "6-10", False, 92, 5000, "phase_1_now", 5)
add("gate_chemical_full", "gate_prep", "GATE Chemical Engineering Complete", "6-10", False, 82, 5000, "phase_1_now", 6)
add("gate_aerospace", "gate_prep", "GATE Aerospace Engineering", "7-10", False, 78, 5000, "phase_1_now", 7)
add("gate_instrumentation", "gate_prep", "GATE Instrumentation Engineering", "6-9", False, 78, 5000, "phase_1_now", 8)
add("gate_metallurgy", "gate_prep", "GATE Metallurgical Engineering", "6-9", False, 72, 5000, "phase_2_2027", 9)
add("gate_biotech", "gate_prep", "GATE Biotechnology", "6-9", False, 76, 5000, "phase_1_now", 10)
add("ese_ies_civil", "ese_ies", "ESE/IES Civil Engineering Paper 1 and 2", "6-10", False, 85, 5000, "phase_1_now", 1)
add("ese_ies_mechanical", "ese_ies", "ESE/IES Mechanical Engineering", "6-10", False, 83, 5000, "phase_1_now", 2)
add("ese_ies_electrical", "ese_ies", "ESE/IES Electrical Engineering", "6-10", False, 83, 5000, "phase_1_now", 3)
add("ese_ies_electronics", "ese_ies", "ESE/IES Electronics and Telecom", "6-10", False, 82, 5000, "phase_1_now", 4)
add("ese_ies_gs_paper", "ese_ies", "ESE/IES General Studies and Engineering Aptitude", "5-8", False, 85, 5000, "phase_1_now", 5)

# Engineering Specializations
add("civil_structural_design", "civil_engineering", "Structural Analysis and Design", "5-9", True, 82, 5000, "phase_1_now", 1)
add("civil_construction_mgmt", "civil_engineering", "Construction Management and Project Planning", "5-8", False, 80, 5000, "phase_1_now", 2)
add("civil_soil_mechanics", "civil_engineering", "Soil Mechanics and Foundation Engineering", "5-9", True, 80, 5000, "phase_1_now", 3)
add("civil_hydraulics", "civil_engineering", "Fluid Mechanics and Hydraulics", "5-9", True, 80, 5000, "phase_1_now", 4)
add("civil_transportation", "civil_engineering", "Transportation Engineering and Highway Design", "5-8", False, 78, 5000, "phase_1_now", 5)
add("mech_thermodynamics_adv", "mechanical_engineering", "Advanced Thermodynamics and Heat Transfer", "6-9", True, 80, 5000, "phase_1_now", 1)
add("mech_machine_design", "mechanical_engineering", "Machine Design and Manufacturing", "5-9", True, 80, 5000, "phase_1_now", 2)
add("mech_fluid_mechanics", "mechanical_engineering", "Fluid Mechanics for Mechanical Engineers", "5-9", True, 80, 5000, "phase_1_now", 3)
add("mech_industrial_engg", "mechanical_engineering", "Industrial Engineering and Operations Research", "5-8", False, 78, 5000, "phase_1_now", 4)
add("ee_power_systems_adv", "electrical_engineering", "Power Systems Analysis and Protection", "6-9", True, 80, 5000, "phase_1_now", 1)
add("ee_control_systems", "electrical_engineering", "Control Systems Engineering", "6-9", True, 80, 5000, "phase_1_now", 2)
add("ee_machines", "electrical_engineering", "Electrical Machines: DC/AC/Transformers", "5-9", True, 80, 5000, "phase_1_now", 3)
add("ece_signal_processing", "electronics_engineering", "Signals and Systems (DSP)", "6-9", True, 80, 5000, "phase_1_now", 1)
add("ece_vlsi_design", "electronics_engineering", "VLSI Design and Semiconductor Devices", "6-10", True, 80, 5000, "phase_1_now", 2)
add("ece_communication_systems", "electronics_engineering", "Communication Systems: Analog and Digital", "6-9", True, 80, 5000, "phase_1_now", 3)
add("ece_embedded_systems", "electronics_engineering", "Embedded Systems and Microcontrollers", "5-9", False, 82, 5000, "phase_1_now", 4)

# ===========================================================================
# ARCHITECTURE AND DESIGN
# ===========================================================================
add("nata_drawing", "architecture", "NATA Drawing Aptitude Test Prep", "4-8", True, 82, 5000, "phase_1_now", 1)
add("nata_aesthetic_sensitivity", "architecture", "NATA Aesthetic Sensitivity", "3-7", True, 80, 5000, "phase_1_now", 2)
add("b_arch_history", "architecture", "B.Arch History of Architecture", "4-8", False, 78, 5000, "phase_1_now", 3)
add("b_arch_building_materials", "architecture", "Building Materials and Construction Technology", "4-8", True, 78, 5000, "phase_1_now", 4)
add("b_arch_structures", "architecture", "Structural Systems in Architecture", "5-9", True, 76, 5000, "phase_1_now", 5)
add("b_arch_environmental", "architecture", "Environmental Studies in Building Design", "4-7", False, 74, 5000, "phase_1_now", 6)
add("interior_design_basics", "architecture", "Interior Design Fundamentals and Color Theory", "2-6", True, 76, 5000, "phase_1_now", 7)
add("urban_planning_basics", "architecture", "Urban Planning and Smart City Concepts", "4-8", True, 72, 5000, "phase_2_2027", 8)

# ===========================================================================
# HOTEL MANAGEMENT AND TOURISM
# ===========================================================================
add("nchm_jee_prep", "hospitality_tourism", "NCHMCT JEE Hotel Management Entrance", "4-8", False, 80, 5000, "phase_1_now", 1)
add("hotel_food_beverage", "hospitality_tourism", "Food and Beverage Service Management", "3-7", False, 78, 5000, "phase_1_now", 2)
add("hotel_front_office", "hospitality_tourism", "Front Office Operations and Hotel Management", "3-7", False, 78, 5000, "phase_1_now", 3)
add("hotel_housekeeping", "hospitality_tourism", "Housekeeping and Accommodation Management", "2-6", False, 72, 5000, "phase_1_now", 4)
add("culinary_arts_basics", "hospitality_tourism", "Culinary Arts and Food Technology Basics", "2-6", False, 76, 5000, "phase_1_now", 5)
add("tourism_management", "hospitality_tourism", "Tourism Management and Travel Agency Operations", "3-7", False, 74, 5000, "phase_1_now", 6)
add("iata_travel_diploma", "hospitality_tourism", "IATA Travel and Tourism Diploma Prep", "4-7", False, 72, 5000, "phase_1_now", 7)

# ===========================================================================
# FASHION AND TEXTILE
# ===========================================================================
add("nift_entrance_design", "fashion_design", "NIFT Entrance Creative Ability Test", "3-7", True, 78, 5000, "phase_1_now", 1)
add("nift_gat_exam", "fashion_design", "NIFT General Ability Test (GAT)", "4-7", False, 78, 5000, "phase_1_now", 2)
add("fashion_design_basics", "fashion_design", "Fashion Design Fundamentals and Illustration", "2-6", True, 74, 5000, "phase_1_now", 3)
add("textile_technology", "fashion_design", "Textile Technology and Fabric Science", "3-7", False, 72, 5000, "phase_1_now", 4)
add("fashion_merchandising", "fashion_design", "Fashion Merchandising and Retail Management", "3-7", False, 70, 5000, "phase_2_2027", 5)

# ===========================================================================
# MASS MEDIA AND JOURNALISM
# ===========================================================================
add("iimc_entrance_exam", "media_journalism", "IIMC Entrance Exam Preparation", "5-9", False, 80, 5000, "phase_1_now", 1)
add("journalism_basics", "media_journalism", "Journalism Fundamentals and News Writing", "3-7", False, 78, 5000, "phase_1_now", 2)
add("digital_journalism", "media_journalism", "Digital Journalism and Social Media Reporting", "3-7", False, 78, 5000, "phase_1_now", 3)
add("film_television_production", "media_journalism", "Film and TV Production Basics (FTII/SRFTI)", "4-8", False, 74, 5000, "phase_1_now", 4)
add("public_relations_basics", "media_journalism", "Public Relations and Corporate Communication", "3-7", False, 72, 5000, "phase_1_now", 5)
add("advertising_copy", "media_journalism", "Advertising and Copywriting Fundamentals", "3-7", False, 72, 5000, "phase_1_now", 6)

# ===========================================================================
# SPORTS AND PHYSICAL EDUCATION
# ===========================================================================
add("b_ped_physical_education", "sports_education", "B.P.Ed Entrance and Physical Education Theory", "3-7", False, 74, 5000, "phase_1_now", 1)
add("sports_science_basics", "sports_education", "Sports Science and Exercise Physiology", "4-8", False, 74, 5000, "phase_1_now", 2)
add("yoga_certification_full", "sports_education", "Yoga Certification (QCI/YCB) Complete Prep", "2-7", False, 78, 5000, "phase_1_now", 3)
add("fitness_trainer_cert", "sports_education", "Certified Fitness Trainer (ACE/ACSM) Prep", "3-7", False, 74, 5000, "phase_1_now", 4)
add("sports_coaching_nis", "sports_education", "NIS Sports Coaching Diploma Prep", "4-8", False, 70, 5000, "phase_2_2027", 5)

# ===========================================================================
# AGRICULTURE AND RURAL
# ===========================================================================
add("icar_jrf_srf", "agriculture_exams", "ICAR JRF/SRF Agricultural Sciences", "6-9", False, 78, 5000, "phase_1_now", 1)
add("agri_officer_nabard", "agriculture_exams", "Agriculture Officer Exam (NABARD/IFFCO)", "5-8", False, 78, 5000, "phase_1_now", 2)
add("agri_horticulture", "agriculture_exams", "Horticulture Science and Crop Management", "4-8", False, 76, 5000, "phase_1_now", 3)
add("agri_soil_water", "agriculture_exams", "Soil Science and Water Management", "4-8", True, 74, 5000, "phase_1_now", 4)
add("agri_animal_husbandry", "agriculture_exams", "Animal Husbandry and Veterinary Basics", "3-7", False, 74, 5000, "phase_1_now", 5)
add("agri_fisheries", "agriculture_exams", "Fisheries Science and Aquaculture", "3-7", False, 70, 5000, "phase_2_2027", 6)
add("agri_rural_development", "agriculture_exams", "Rural Development Schemes and MNREGA", "3-7", False, 76, 5000, "phase_1_now", 7)

# ===========================================================================
# CA FINAL AND ADVANCED PROFESSIONAL
# ===========================================================================
add("ca_final_sfm", "ca_final", "CA Final Strategic Financial Management", "7-10", False, 85, 5000, "phase_1_now", 1)
add("ca_final_audit_ethics", "ca_final", "CA Final Audit, Assurance and Ethics", "7-10", False, 83, 5000, "phase_1_now", 2)
add("ca_final_tax_law", "ca_final", "CA Final Direct and Indirect Tax Laws", "7-10", False, 85, 5000, "phase_1_now", 3)
add("ca_final_corporate_law", "ca_final", "CA Final Corporate and Economic Laws", "7-10", False, 82, 5000, "phase_1_now", 4)
add("ca_final_costing", "ca_final", "CA Final Advanced Costing and Management", "7-10", False, 82, 5000, "phase_1_now", 5)
add("ca_final_financial_reporting", "ca_final", "CA Final Financial Reporting (Ind AS/IFRS)", "7-10", False, 85, 5000, "phase_1_now", 6)
add("ifrs_full_course", "advanced_finance", "IFRS International Financial Reporting Standards", "6-10", False, 80, 5000, "phase_1_now", 1)
add("us_cpa_far", "advanced_finance", "US CPA FAR (Financial Accounting and Reporting)", "7-10", False, 78, 5000, "phase_1_now", 2)
add("us_cpa_aud", "advanced_finance", "US CPA AUD (Auditing and Attestation)", "7-10", False, 76, 5000, "phase_1_now", 3)
add("us_cpa_bec", "advanced_finance", "US CPA BEC (Business Environment Concepts)", "6-9", False, 76, 5000, "phase_1_now", 4)
add("us_cpa_reg", "advanced_finance", "US CPA REG (Regulation and Tax Law)", "7-10", False, 74, 5000, "phase_1_now", 5)

# ===========================================================================
# UPSC MAINS AND ADVANCED
# ===========================================================================
add("upsc_mains_gs1_history", "upsc_mains", "UPSC Mains GS Paper 1: History and Geography", "7-10", False, 90, 5000, "phase_1_now", 1)
add("upsc_mains_gs2_polity", "upsc_mains", "UPSC Mains GS Paper 2: Polity and IR", "7-10", False, 90, 5000, "phase_1_now", 2)
add("upsc_mains_gs3_economy", "upsc_mains", "UPSC Mains GS Paper 3: Economy and Technology", "7-10", False, 90, 5000, "phase_1_now", 3)
add("upsc_mains_gs4_ethics", "upsc_mains", "UPSC Mains GS Paper 4: Ethics and Integrity", "7-10", False, 88, 5000, "phase_1_now", 4)
add("upsc_essay_writing", "upsc_mains", "UPSC Essay Paper Writing Techniques", "6-10", False, 88, 5000, "phase_1_now", 5)
add("upsc_optional_sociology", "upsc_mains", "UPSC Optional: Sociology Paper 1 and 2", "7-10", False, 82, 5000, "phase_1_now", 6)
add("upsc_optional_history", "upsc_mains", "UPSC Optional: History Paper 1 and 2", "7-10", False, 82, 5000, "phase_1_now", 7)
add("upsc_optional_geography", "upsc_mains", "UPSC Optional: Geography Paper 1 and 2", "7-10", False, 82, 5000, "phase_1_now", 8)
add("upsc_optional_polsci", "upsc_mains", "UPSC Optional: Political Science and IR", "7-10", False, 80, 5000, "phase_1_now", 9)
add("upsc_optional_pub_admin", "upsc_mains", "UPSC Optional: Public Administration", "7-10", False, 80, 5000, "phase_1_now", 10)
add("upsc_optional_anthropology", "upsc_mains", "UPSC Optional: Anthropology", "7-10", False, 78, 5000, "phase_1_now", 11)
add("upsc_optional_law", "upsc_mains", "UPSC Optional: Law Paper 1 and 2", "7-10", False, 78, 5000, "phase_1_now", 12)
add("upsc_optional_maths", "upsc_mains", "UPSC Optional: Mathematics", "8-10", False, 76, 5000, "phase_1_now", 13)
add("upsc_optional_physics", "upsc_mains", "UPSC Optional: Physics", "8-10", False, 74, 5000, "phase_1_now", 14)
add("upsc_interview_personality", "upsc_mains", "UPSC Personality Test and Interview Prep", "5-9", False, 85, 5000, "phase_1_now", 15)

# ===========================================================================
# RESEARCH AND ACADEMIA
# ===========================================================================
add("ugc_net_paper1", "research_academia", "UGC NET Paper 1: Teaching and Research Aptitude", "5-9", False, 85, 5000, "phase_1_now", 1)
add("ugc_net_education", "research_academia", "UGC NET Education Paper 2", "6-9", False, 80, 5000, "phase_1_now", 2)
add("ugc_net_english", "research_academia", "UGC NET English Literature", "6-9", False, 80, 5000, "phase_1_now", 3)
add("ugc_net_history", "research_academia", "UGC NET History", "6-9", False, 78, 5000, "phase_1_now", 4)
add("ugc_net_sociology", "research_academia", "UGC NET Sociology", "6-9", False, 78, 5000, "phase_1_now", 5)
add("ugc_net_economics", "research_academia", "UGC NET Economics", "6-9", False, 78, 5000, "phase_1_now", 6)
add("ugc_net_political_science", "research_academia", "UGC NET Political Science", "6-9", False, 76, 5000, "phase_1_now", 7)
add("ugc_net_commerce", "research_academia", "UGC NET Commerce and Management", "6-9", False, 78, 5000, "phase_1_now", 8)
add("ugc_net_computer_science", "research_academia", "UGC NET Computer Science", "6-9", False, 82, 5000, "phase_1_now", 9)
add("phd_entrance_common", "research_academia", "PhD Entrance Exam Preparation (General)", "6-10", False, 78, 5000, "phase_1_now", 10)
add("research_methodology", "research_academia", "Research Methodology and Statistics for PhD", "5-9", False, 76, 5000, "phase_1_now", 11)

# ===========================================================================
# ENTREPRENEUR AND STARTUP
# ===========================================================================
add("startup_legal_basics", "entrepreneurship", "Startup Legal Essentials: Registrations and Compliance", "3-7", False, 80, 5000, "phase_1_now", 1)
add("startup_funding_vc", "entrepreneurship", "Startup Funding: Angel, VC and Series A", "4-8", False, 80, 5000, "phase_1_now", 2)
add("startup_product_management", "entrepreneurship", "Product Management for Startups", "4-8", False, 82, 5000, "phase_1_now", 3)
add("startup_growth_hacking", "entrepreneurship", "Growth Hacking and Customer Acquisition", "4-7", False, 78, 5000, "phase_1_now", 4)
add("startup_business_plan", "entrepreneurship", "Business Plan and Financial Projections", "4-8", False, 78, 5000, "phase_1_now", 5)
add("msme_schemes_india", "entrepreneurship", "MSME Schemes, Mudra Loans and Government Support", "2-6", False, 80, 5000, "phase_1_now", 6)
add("ecommerce_amazon_flipkart", "entrepreneurship", "Selling on Amazon and Flipkart (Complete Guide)", "2-6", False, 78, 5000, "phase_1_now", 7)
add("freelancing_upwork_fiverr", "entrepreneurship", "Freelancing on Upwork and Fiverr (Indian Guide)", "2-6", False, 80, 5000, "phase_1_now", 8)

# ===========================================================================
# CURRENT AFFAIRS — Comprehensive
# ===========================================================================
add("current_affairs_monthly", "current_affairs_full", "Monthly Current Affairs for All Exams", "3-7", False, 95, 5000, "phase_1_now", 1)
add("current_affairs_economy_budget", "current_affairs_full", "Union Budget, Economic Survey and Finance", "4-8", False, 92, 5000, "phase_1_now", 2)
add("current_affairs_international", "current_affairs_full", "International Relations and World Affairs", "4-8", False, 90, 5000, "phase_1_now", 3)
add("current_affairs_science_tech", "current_affairs_full", "Science, Technology and Space Current Affairs", "3-7", False, 90, 5000, "phase_1_now", 4)
add("current_affairs_sports", "current_affairs_full", "Sports Current Affairs and Championships", "2-5", False, 88, 5000, "phase_1_now", 5)
add("current_affairs_awards_appointments", "current_affairs_full", "Awards, Appointments and Rankings", "2-5", False, 88, 5000, "phase_1_now", 6)
add("current_affairs_schemes_govt", "current_affairs_full", "Government Schemes and Policies", "3-7", False, 90, 5000, "phase_1_now", 7)
add("static_gk_complete", "current_affairs_full", "Static GK: Complete Reference for All Exams", "3-7", False, 92, 5000, "phase_1_now", 8)

print(f"\nTotal topics prepared: {len(ALL_TOPICS)}")
print("Starting insertion...")

# ── INSERT IN BATCHES OF 50 ───────────────────────────────────────────────
BATCH = 50
inserted = 0
skipped = 0
errors = 0

for i in range(0, len(ALL_TOPICS), BATCH):
    batch = ALL_TOPICS[i:i+BATCH]
    try:
        r = requests.post(
            f'{u}/rest/v1/topics',
            headers=h,
            json=batch,
            timeout=30
        )
        if r.status_code in [200, 201]:
            inserted += len(batch)
            print(f'Batch {i//BATCH+1}/{(len(ALL_TOPICS)+BATCH-1)//BATCH}: +{len(batch)} OK (total: {inserted})')
        elif r.status_code == 409:
            skipped += len(batch)
            print(f'Batch {i//BATCH+1}: {len(batch)} already exist')
        else:
            errors += len(batch)
            print(f'Batch {i//BATCH+1}: ERROR {r.status_code}: {r.text[:150]}')
    except Exception as e:
        errors += len(batch)
        print(f'Batch {i//BATCH+1}: EXCEPTION: {e}')

print(f'\n{"="*50}')
print(f'DONE: {inserted} inserted | {skipped} skipped | {errors} errors')
print(f'Total topics added this run: {inserted}')
