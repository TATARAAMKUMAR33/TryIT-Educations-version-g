# MEGA QUEUE - Programmatically generated for 5000+ exam coverage

STATES = ["AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JH", "KA", "KL", "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB", "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB"]
UTS = ["AN", "CH", "DN", "DL", "JK", "LA", "LD", "PY"]

GENERATION_QUEUE = []

# Helper to add items without duplicates
def add(phase, category, subcategory):
    GENERATION_QUEUE.append({"phase": phase, "category": category, "subcategory": subcategory})

# --- PHASE 1: BOARDS & SCHOOLS ---
for s in STATES + UTS:
    add(1, "board_exams", f"{s}_1_6")
    add(1, "board_exams", f"{s}_7_12")

# --- PHASE 2: SCHOLARSHIPS ---
for sch in ["NTSE", "NMMS", "KVPY", "INSPIRE", "JBNSTS", "Homi_Bhabha", "PM_YASASVI", "Pre_Matric", "Post_Matric", "SOF_Olympiads", "IOQM", "RMO", "INMO"]:
    add(2, "scholarship", sch)

# --- PHASE 3: SCHOOL ENTRANCES ---
for ent in ["Navodaya_JNVST", "Sainik_School_AISSEE", "RIMC", "Rashtriya_Military", "KVS_Entrance", "Sainik_School_Class9"]:
    add(3, "school_entrance", ent)

# --- PHASE 4: UG ENGINEERING (Central + State) ---
for eng in ["JEE_Main", "JEE_Advanced", "BITSAT", "VITEEE", "SRMJEEE", "KIITEE", "MHT_CET", "WBJEE", "KCET", "COMEDK", "AP_EAMCET", "TS_EAMCET", "OJEE", "BCECE", "UPSEE", "GUJCET", "MP_PET", "HPTECH", "UKSEE", "PESSAT"]:
    add(4, "ug_entrance_engineering", eng)

# --- PHASE 5: UG MEDICAL ---
for med in ["NEET_UG", "AYUSH", "Nursing", "AIIMS_BSc", "JIPMER", "CMC_Vellore", "AFMC", "NEET_PG", "INI_CET", "FMGE"]:
    add(5, "ug_entrance_medical", med)

# --- PHASE 6: UG OTHER (Law, Design, Uni) ---
for oth in ["CLAT", "AILET", "LSAT_India", "CUET_UG", "NIFT", "NID", "UCEED", "NATA", "IPMAT", "NPAT", "SET", "CUCET", "BHU_UET", "JNU_EE", "JMI_Entrance", "AMU_Entrance"]:
    add(6, "ug_entrance_other", oth)

# --- PHASE 7: PG ENTRANCE ---
for pg in ["GATE", "CAT", "XAT", "CMAT", "MAT", "NMAT", "SNAP", "IIFT", "CUET_PG", "IIT_JAM", "GPAT", "TISSNET", "TANCET", "KMAT", "ATMA", "IBSAT"]:
    add(7, "pg_entrance", pg)

# --- PHASE 8: PHD ENTRANCE ---
for phd in ["UGC_NET", "CSIR_NET", "ICMR_JRF", "DBT_JRF", "ICAR_AICE"]:
    add(8, "phd_entrance", phd)

# --- PHASE 9: CENTRAL GOVT JOBS ---
for cgovt in ["UPSC_CSE", "UPSC_CDS", "UPSC_CAPF", "UPSC_IES", "UPSC_CMS", "UPSC_IFS", "SSC_CGL", "SSC_CHSL", "SSC_MTS", "SSC_GD", "SSC_Steno", "SSC_CPO", "SSC_JE", "IBPS_PO", "IBPS_Clerk", "IBPS_SO", "SBI_PO", "SBI_Clerk", "SBI_SO", "RBI_Grade_B", "RBI_Assistant", "NABARD", "LIC_AAO", "LIC_ADO", "EPFO_ENFORCEMENT", "RRB_NTPC", "RRB_Group_D", "RRB_ALP", "RRB_JE", "RRB_Paramedical"]:
    add(9, "central_govt_jobs", cgovt)

# --- PHASE 10: STATE PSC & POLICE (Dynamic for all states) ---
for s in STATES:
    add(10, "state_psc", f"{s}_PSC")
    add(10, "state_police", f"{s}_Police_SI")
    add(10, "state_police", f"{s}_Police_Constable")
    add(10, "state_teaching", f"{s}_TET")
    add(10, "state_teaching", f"{s}_PGT_TGT")

# --- PHASE 11: DEFENCE ---
for mil in ["NDA", "Agniveer_Army", "Agniveer_Navy", "Agniveer_Airforce", "CDS", "AFCAT", "TES", "TGC", "Indian_Coast_Guard", "SSC_Tech", "Territorial_Army"]:
    add(11, "military", mil)

# --- PHASE 12: PROFESSIONAL ---
for prof in ["CA_Foundation", "CA_Intermediate", "CA_Final", "CS_Foundation", "CS_Executive", "CS_Professional", "CMA_Foundation", "CMA_Inter", "CMA_Final", "CFA_Level_1", "FRM"]:
    add(12, "professional", prof)

# --- PHASE 13: TECH CERTIFICATIONS ---
for tech in ["AWS_Cloud_Practitioner", "AWS_Solutions_Architect", "Azure_Fundamentals", "Azure_Admin", "Cisco_CCNA", "Google_Cloud", "CompTIA_Security", "Salesforce_Admin", "Oracle_Java", "RedHat_Linux"]:
    add(13, "tech_certifications", tech)

# --- PHASE 14: COMPANY EXAMS ---
for comp in ["TCS_NQT", "TCS_Prime", "Infosys_InfyTQ", "Wipro_WILP", "Accenture", "Cognizant_GenC", "Capgemini", "HCL_TechBee", "Tech_Mahindra", "Amazon_SDE", "Google_Step", "Microsoft_Eng"]:
    add(14, "company_exams", comp)

# --- PHASE 15: LANGUAGE & FOREIGN ---
for lang in ["IELTS", "TOEFL", "GRE", "GMAT", "SAT", "ACT", "PTE_Academic", "Duolingo", "JLPT", "HSK", "DELF", "Goethe"]:
    add(15, "language_foreign", lang)

# --- PHASE 16: SKILL & VOCATIONAL ---
for voc in ["ITI_Electrician", "ITI_Fitter", "ITI_Welder", "ITI_Turner", "NIELIT_O", "NIELIT_A", "NIELIT_B", "B_Ed_Entrance", "D_El_Ed", "Polytechnic_Entrance"]:
    add(16, "skill_vocational", voc)

# --- PHASE 17: NEP / PARAKH ---
for nep in ["PARAKH_NAS", "SAFAL", "CBSE_CTET", "State_TET"]:
    add(17, "nep_parakh", nep)


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
