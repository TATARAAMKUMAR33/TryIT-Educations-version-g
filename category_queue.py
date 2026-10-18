GENERATION_QUEUE = [
    # PHASE 1: BOARD EXAMS (Class 1 to 12)
    {"phase": 1, "category": "board_exams", "subcategory": "CBSE",              "desc": "Central Board of Secondary Education — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "ICSE_ISC",          "desc": "CISCE — ICSE Class 1 to 10 & ISC Class 11-12"},
    {"phase": 1, "category": "board_exams", "subcategory": "NIOS",              "desc": "National Institute of Open Schooling — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "IB",                "desc": "International Baccalaureate — PYP, MYP, DP"},
    {"phase": 1, "category": "board_exams", "subcategory": "IGCSE",             "desc": "Cambridge IGCSE & A-Levels — Primary to Advanced"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_TN",          "desc": "Tamil Nadu State Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_MH",          "desc": "Maharashtra SSC & HSC Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_UP",          "desc": "UP Madhyamik Shiksha Parishad — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_KA",          "desc": "Karnataka SSLC & PUC Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_AP",          "desc": "Andhra Pradesh SSC & Intermediate Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_TS",          "desc": "Telangana SSC & Intermediate Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_KL",          "desc": "Kerala SSLC & Plus Two Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_WB",          "desc": "West Bengal Madhyamik & Higher Secondary — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_RJ",          "desc": "Rajasthan Board of Secondary Education — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_GJ",          "desc": "Gujarat Secondary & Higher Secondary Board — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_MP",          "desc": "Madhya Pradesh Board of Secondary Education — Class 1 to 12"},
    {"phase": 1, "category": "board_exams", "subcategory": "state_BR",          "desc": "Bihar School Examination Board — Class 1 to 12"},

    # PHASE 2: SCHOLARSHIPS
    {"phase": 2, "category": "scholarship", "subcategory": "NTSE",              "desc": "National Talent Search Examination — Class 10"},
    {"phase": 2, "category": "scholarship", "subcategory": "NMMS",              "desc": "National Means-cum-Merit Scholarship — Class 8"},
    {"phase": 2, "category": "scholarship", "subcategory": "KVPY",              "desc": "Kishore Vaigyanik Protsahan Yojana"},
    {"phase": 2, "category": "scholarship", "subcategory": "NSO_IMO_IEO",       "desc": "SOF Olympiads — Science, Maths, English"},

    # PHASE 3: SCHOOL ENTRANCES
    {"phase": 3, "category": "school_entrance", "subcategory": "navodaya_JNV",  "desc": "Jawahar Navodaya Vidyalaya — Class 6 & 9"},
    {"phase": 3, "category": "school_entrance", "subcategory": "sainik_school", "desc": "Sainik School Entrance — Class 6 & 9 (AISSEE)"},

    # PHASE 4: UG ENGINEERING
    {"phase": 4, "category": "ug_entrance_engineering", "subcategory": "JEE_Main",    "desc": "Joint Entrance Examination Main — NTA"},
    {"phase": 4, "category": "ug_entrance_engineering", "subcategory": "JEE_Advanced","desc": "JEE Advanced — IIT entrance"},
    {"phase": 4, "category": "ug_entrance_engineering", "subcategory": "BITSAT",      "desc": "BITS Pilani entrance"},
    {"phase": 4, "category": "ug_entrance_engineering", "subcategory": "State_CETs",  "desc": "MHT-CET, KCET, WBJEE, AP EAMCET, TS EAMCET, GUJCET"},

    # PHASE 5: UG MEDICAL & ALLIED HEALTH
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "NEET_UG",     "desc": "National Eligibility cum Entrance Test — UG"},
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "AYUSH",       "desc": "BAMS, BHMS, BSMS, BUMS entrance"},
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "Physiotherapy","desc": "BPT Entrance"},
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "Nursing",     "desc": "B.Sc Nursing Entrance"},
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "Pharmacy",    "desc": "B.Pharm Entrance"},
    {"phase": 5, "category": "ug_entrance_medical", "subcategory": "Veterinary",  "desc": "BVSc & AH Entrance"},

    # PHASE 6: UG OTHER STREAMS
    {"phase": 6, "category": "ug_entrance_other", "subcategory": "CLAT",         "desc": "Common Law Admission Test"},
    {"phase": 6, "category": "ug_entrance_other", "subcategory": "IPMAT",        "desc": "Integrated Programme in Management — IIM"},
    {"phase": 6, "category": "ug_entrance_other", "subcategory": "NIFT_NID",     "desc": "Design Entrance — NIFT, NID, UCEED"},
    {"phase": 6, "category": "ug_entrance_other", "subcategory": "NATA",         "desc": "National Aptitude Test in Architecture"},
    {"phase": 6, "category": "ug_entrance_other", "subcategory": "CUET_UG",      "desc": "Common University Entrance Test — UG"},

    # PHASE 7: PG ENTRANCES (All MBA Variants)
    {"phase": 7, "category": "pg_entrance", "subcategory": "GATE",              "desc": "Graduate Aptitude Test in Engineering"},
    {"phase": 7, "category": "pg_entrance", "subcategory": "CAT",               "desc": "Common Admission Test — IIMs"},
    {"phase": 7, "category": "pg_entrance", "subcategory": "MBA_Variants",      "desc": "Executive MBA, Online MBA, Distance MBA, PGDM"},
    {"phase": 7, "category": "pg_entrance", "subcategory": "NEET_PG",           "desc": "NEET PG — Medical postgraduate"},
    {"phase": 7, "category": "pg_entrance", "subcategory": "CUET_PG",           "desc": "Common University Entrance Test PG"},
    {"phase": 7, "category": "pg_entrance", "subcategory": "UGC_NET",           "desc": "UGC NET — Lectureship & JRF"},

    # PHASE 8: PhD ENTRANCES
    {"phase": 8, "category": "phd_entrance", "subcategory": "CSIR_NET",         "desc": "CSIR UGC NET — Science subjects"},
    {"phase": 8, "category": "phd_entrance", "subcategory": "University_PhD",   "desc": "University-specific PhD entrance — IIT, IISc, etc."},

    # PHASE 9: CENTRAL GOVT JOBS
    {"phase": 9, "category": "central_govt_jobs", "subcategory": "UPSC_IAS",    "desc": "Civil Services Examination — IAS/IPS/IFS"},
    {"phase": 9, "category": "central_govt_jobs", "subcategory": "SSC_CGL",     "desc": "Staff Selection Commission Combined Graduate Level"},
    {"phase": 9, "category": "central_govt_jobs", "subcategory": "IBPS_PO",     "desc": "IBPS Probationary Officer"},
    {"phase": 9, "category": "central_govt_jobs", "subcategory": "RRB_NTPC",    "desc": "Railway Recruitment Board NTPC"},

    # PHASE 10: STATE PSCs
    {"phase": 10, "category": "state_psc", "subcategory": "TNPSC",              "desc": "Tamil Nadu Public Service Commission"},
    {"phase": 10, "category": "state_psc", "subcategory": "UPPSC",              "desc": "Uttar Pradesh PSC"},
    {"phase": 10, "category": "state_psc", "subcategory": "MPSC",               "desc": "Maharashtra PSC"},
    {"phase": 10, "category": "state_psc", "subcategory": "KPSC",               "desc": "Karnataka PSC"},
    {"phase": 10, "category": "state_psc", "subcategory": "BPSC",               "desc": "Bihar PSC"},

    # PHASE 11: DEFENCE & POLICE
    {"phase": 11, "category": "military", "subcategory": "NDA",                 "desc": "National Defence Academy"},
    {"phase": 11, "category": "military", "subcategory": "Agniveer",            "desc": "Agniveer Army, Navy, Air Force"},
    {"phase": 11, "category": "military", "subcategory": "State_Police",        "desc": "State Police SI/Constable"},

    # PHASE 12: PROFESSIONAL
    {"phase": 12, "category": "professional", "subcategory": "CA_Foundation",   "desc": "ICAI CA Foundation"},
    {"phase": 12, "category": "professional", "subcategory": "CS_Executive",    "desc": "ICSI CS Executive"},
    {"phase": 12, "category": "professional", "subcategory": "CMA",             "desc": "ICMAI CMA"},

    # PHASE 13: TECH CERTIFICATIONS
    {"phase": 13, "category": "tech_certifications", "subcategory": "AWS",      "desc": "Amazon Web Services Certifications"},
    {"phase": 13, "category": "tech_certifications", "subcategory": "Azure",    "desc": "Microsoft Azure Certifications"},

    # PHASE 14: PRIVATE COMPANIES
    {"phase": 14, "category": "company_exams", "subcategory": "TCS_NQT",        "desc": "TCS National Qualifier Test"},
    {"phase": 14, "category": "company_exams", "subcategory": "Infosys",        "desc": "Infosys InfyTQ"},

    # PHASE 15: FOREIGN & LANGUAGE
    {"phase": 15, "category": "language_foreign", "subcategory": "IELTS",       "desc": "IELTS Academic & General Training"},
    {"phase": 15, "category": "language_foreign", "subcategory": "GRE",         "desc": "GRE General Test"},

    # PHASE 16: SKILL & VOCATIONAL
    {"phase": 16, "category": "skill_vocational", "subcategory": "ITI_trades",  "desc": "All ITI trades — NCVT & SCVT"},

    # PHASE 17: NEP & PARAKH
    {"phase": 17, "category": "nep_parakh", "subcategory": "PARAKH_NAS",        "desc": "PARAKH — National Achievement Survey"}
]

def get_queue_by_phase(phase: int) -> list:
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
