GENERATION_QUEUE = [
    # PHASE 1A: BOARD EXAMS (Class 1-6)
    {"phase": "1a", "category": "board_exams", "subcategory": "CBSE_1_6", "desc": "CBSE Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1, Class 2, Class 3, Class 4, Class 5, Class 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "ICSE_1_6", "desc": "ICSE Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1, Class 2, Class 3, Class 4, Class 5, Class 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "NIOS_1_6", "desc": "NIOS Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1 to Class 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "IB_1_6",   "desc": "IB PYP & MYP", "prompt_rule": "Generate exactly 6 exams for PYP Year 1-6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "TN_1_6",   "desc": "TN Board Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1 to 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "MH_1_6",   "desc": "MH Board Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1 to 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "UP_1_6",   "desc": "UP Board Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1 to 6."},
    {"phase": "1a", "category": "board_exams", "subcategory": "KA_1_6",   "desc": "KA Board Class 1 to 6", "prompt_rule": "Generate exactly 6 exams: Class 1 to 6."},

    # PHASE 1B: BOARD EXAMS (Class 7-12)
    {"phase": "1b", "category": "board_exams", "subcategory": "CBSE_7_12", "desc": "CBSE Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7, Class 8, Class 9, Class 10, Class 11, Class 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "ICSE_7_12", "desc": "ICSE Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "NIOS_7_12", "desc": "NIOS Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "IB_7_12",   "desc": "IB DP", "prompt_rule": "Generate exactly 6 exams for DP Year 1-2 and MYP Year 4-5."},
    {"phase": "1b", "category": "board_exams", "subcategory": "TN_7_12",   "desc": "TN Board Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "MH_7_12",   "desc": "MH Board Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "UP_7_12",   "desc": "UP Board Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},
    {"phase": "1b", "category": "board_exams", "subcategory": "KA_7_12",   "desc": "KA Board Class 7 to 12", "prompt_rule": "Generate exactly 6 exams: Class 7 to 12."},

    # PHASE 2: SCHOLARSHIPS
    {"phase": "2", "category": "scholarship", "subcategory": "NTSE", "desc": "National Talent Search", "prompt_rule": "Generate NTSE Stage 1 and Stage 2."},
    {"phase": "2", "category": "scholarship", "subcategory": "NMMS", "desc": "Means-cum-Merit", "prompt_rule": "Generate NMMS Class 8 exam."},
    {"phase": "2", "category": "scholarship", "subcategory": "KVPY", "desc": "KVPY", "prompt_rule": "Generate KVPY Streams SA, SX, SB."},
    {"phase": "2", "category": "scholarship", "subcategory": "SOF_Olympiads", "desc": "SOF", "prompt_rule": "Generate NSO, IMO, IEO."},

    # PHASE 3: SCHOOL ENTRANCES
    {"phase": "3", "category": "school_entrance", "subcategory": "Navodaya", "desc": "JNVST", "prompt_rule": "Generate Class 6 and Class 9 JNVST exams."},
    {"phase": "3", "category": "school_entrance", "subcategory": "Sainik_School", "desc": "AISSEE", "prompt_rule": "Generate Class 6 and Class 9 AISSEE exams."},

    # PHASE 4: UG ENGINEERING
    {"phase": "4", "category": "ug_entrance_engineering", "subcategory": "JEE_Main", "desc": "JEE Main", "prompt_rule": "Generate JEE Main Paper 1 and Paper 2."},
    {"phase": "4", "category": "ug_entrance_engineering", "subcategory": "JEE_Advanced", "desc": "JEE Advanced", "prompt_rule": "Generate JEE Advanced Paper 1 and Paper 2."},
    {"phase": "4", "category": "ug_entrance_engineering", "subcategory": "BITSAT", "desc": "BITSAT", "prompt_rule": "Generate BITSAT exam."},

    # PHASE 5: UG MEDICAL & ALLIED
    {"phase": "5", "category": "ug_entrance_medical", "subcategory": "NEET_UG", "desc": "NEET UG", "prompt_rule": "Generate NEET UG exam."},
    {"phase": "5", "category": "ug_entrance_medical", "subcategory": "AYUSH", "desc": "AYUSH", "prompt_rule": "Generate AACCC AYUSH exam."},
    {"phase": "5", "category": "ug_entrance_medical", "subcategory": "Nursing", "desc": "Nursing", "prompt_rule": "Generate B.Sc Nursing entrance."},

    # PHASE 6: UG OTHER
    {"phase": "6", "category": "ug_entrance_other", "subcategory": "CLAT", "desc": "CLAT", "prompt_rule": "Generate CLAT UG exam."},
    {"phase": "6", "category": "ug_entrance_other", "subcategory": "CUET_UG", "desc": "CUET UG", "prompt_rule": "Generate CUET UG exams for top 5 subjects."},

    # PHASE 7: PG ENTRANCES
    {"phase": "7", "category": "pg_entrance", "subcategory": "GATE", "desc": "GATE", "prompt_rule": "Generate GATE exams for top 5 branches (CS, ME, CE, EE, EC)."},
    {"phase": "7", "category": "pg_entrance", "subcategory": "CAT", "desc": "CAT", "prompt_rule": "Generate CAT exam."},
    {"phase": "7", "category": "pg_entrance", "subcategory": "MBA_Variants", "desc": "Other MBA", "prompt_rule": "Generate XAT, CMAT, MAT, SNAP, NMAT."},
    {"phase": "7", "category": "pg_entrance", "subcategory": "CUET_PG", "desc": "CUET PG", "prompt_rule": "Generate CUET PG exams."},

    # PHASE 8: PhD
    {"phase": "8", "category": "phd_entrance", "subcategory": "UGC_NET", "desc": "UGC NET", "prompt_rule": "Generate UGC NET Paper 1 and Paper 2."},
    {"phase": "8", "category": "phd_entrance", "subcategory": "CSIR_NET", "desc": "CSIR NET", "prompt_rule": "Generate CSIR NET exams."},

    # PHASE 9: CENTRAL GOVT
    {"phase": "9", "category": "central_govt_jobs", "subcategory": "UPSC_CSE", "desc": "UPSC CSE", "prompt_rule": "Generate UPSC Prelims and Mains (generate 2 exams)."},
    {"phase": "9", "category": "central_govt_jobs", "subcategory": "SSC_CGL", "desc": "SSC CGL", "prompt_rule": "Generate SSC CGL Tier 1 and Tier 2."},
    {"phase": "9", "category": "central_govt_jobs", "subcategory": "IBPS_PO", "desc": "IBPS PO", "prompt_rule": "Generate IBPS PO Prelims and Mains."},

    # PHASE 10: STATE PSC
    {"phase": "10", "category": "state_psc", "subcategory": "TNPSC", "desc": "TNPSC", "prompt_rule": "Generate TNPSC Group 1, 2, 4."},
    {"phase": "10", "category": "state_psc", "subcategory": "UPPSC", "desc": "UPPSC", "prompt_rule": "Generate UPPSC PCS Prelims and Mains."},

    # PHASE 11: MILITARY
    {"phase": "11", "category": "military", "subcategory": "NDA", "desc": "NDA", "prompt_rule": "Generate NDA exam."},
    {"phase": "11", "category": "military", "subcategory": "Agniveer", "desc": "Agniveer", "prompt_rule": "Generate Agniveer Army, Navy, Air Force."},

    # PHASE 12: PROFESSIONAL
    {"phase": "12", "category": "professional", "subcategory": "CA", "desc": "CA", "prompt_rule": "Generate CA Foundation, Inter, Final."},
    {"phase": "12", "category": "professional", "subcategory": "CS", "desc": "CS", "prompt_rule": "Generate CS Executive and Professional."},

    # PHASE 13: TECH
    {"phase": "13", "category": "tech_certifications", "subcategory": "AWS", "desc": "AWS", "prompt_rule": "Generate AWS Cloud Practitioner and Solutions Architect."},
    {"phase": "13", "category": "tech_certifications", "subcategory": "Azure", "desc": "Azure", "prompt_rule": "Generate AZ-900 and AZ-104."},

    # PHASE 14: COMPANIES
    {"phase": "14", "category": "company_exams", "subcategory": "TCS", "desc": "TCS NQT", "prompt_rule": "Generate TCS NQT exam."},
    {"phase": "14", "category": "company_exams", "subcategory": "Infosys", "desc": "Infosys", "prompt_rule": "Generate Infosys InfyTQ exam."},

    # PHASE 15: FOREIGN
    {"phase": "15", "category": "language_foreign", "subcategory": "IELTS", "desc": "IELTS", "prompt_rule": "Generate IELTS Academic and General."},
    {"phase": "15", "category": "language_foreign", "subcategory": "GRE", "desc": "GRE", "prompt_rule": "Generate GRE General Test."},

    # PHASE 16: SKILL
    {"phase": "16", "category": "skill_vocational", "subcategory": "ITI", "desc": "ITI", "prompt_rule": "Generate ITI Fitter, Electrician, Welder."},

    # PHASE 17: NEP
    {"phase": "17", "category": "nep_parakh", "subcategory": "PARAKH", "desc": "PARAKH", "prompt_rule": "Generate PARAKH NAS exam."}
]

def get_queue_by_phase(phase: str) -> list:
    return [q for q in GENERATION_QUEUE if q["phase"] == phase]

def get_queue_by_phase(phase: str) -> list:
    return [q for q in GENERATION_QUEUE if q["phase"] == phase]

def get_queue_by_category(category: str) -> list:
    return [q for q in GENERATION_QUEUE if q["category"] == category]

def get_all_categories() -> list:
    seen = set()
    cats = []
    for q in GENERATION_QUEUE:
        if q["category"] not in seen:
            cats.append(q["category"])
            seen.add(q["category"])
    return cats

def get_total_count() -> int:
    return len(GENERATION_QUEUE)
