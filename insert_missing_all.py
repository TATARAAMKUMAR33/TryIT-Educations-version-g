"""
insert_missing_all.py
Inserts ALL missing exams, subjects, topics and syllabus maps
State Police, Teaching, PSU, Banking, Agriculture, Legal, Health,
International Medical, Certifications, B2B data layer
"""
import os, requests, uuid, time
from dotenv import load_dotenv
load_dotenv()

u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {
    "apikey": k,
    "Authorization": f"Bearer {k}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates"
}

def post(endpoint, data, retries=3):
    for i in range(retries):
        try:
            r = requests.post(f"{u}/rest/v1/{endpoint}", headers=h,
                            json=data, timeout=90)
            return r
        except Exception as e:
            print(f"  Retry {i+1}: {str(e)[:50]}")
            time.sleep(10)
    return None

def insert_batch(endpoint, rows, label=""):
    ins = skip = err = 0
    for i in range(0, len(rows), 100):
        batch = rows[i:i+100]
        r = post(endpoint, batch)
        if r is None: err += len(batch)
        elif r.status_code in [200,201]: ins += len(batch)
        elif r.status_code == 409: skip += len(batch)
        else:
            err += len(batch)
            print(f"  ERR {r.status_code}: {r.text[:80]}")
    print(f"{label}: {ins} inserted | {skip} skipped | {err} errors")
    return ins

# ══════════════════════════════════════════════════════════════════
# 1. MISSING SUBJECTS
# ══════════════════════════════════════════════════════════════════
NEW_SUBJECTS = [
    # Teaching
    {"subject_id":"ctet_teaching","subject_name":"CTET and Teaching Exams","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    {"subject_id":"state_tet","subject_name":"State TET Exams","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    {"subject_id":"child_development","subject_name":"Child Development and Pedagogy","parent_id":None,"stream":"professional","domain_type":"academic_exam","pillar_id":None},
    # Police
    {"subject_id":"state_police","subject_name":"State Police Exams","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    # Banking extended
    {"subject_id":"banking_extended","subject_name":"Banking and Insurance Extended","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    # PSU Engineering
    {"subject_id":"psu_engineering","subject_name":"PSU Engineering Exams","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    # Revenue/Civil
    {"subject_id":"revenue_civil","subject_name":"Revenue and Civil Services","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    # Legal/Judicial
    {"subject_id":"judicial_exams","subject_name":"Judicial and Legal Services","parent_id":None,"stream":"professional","domain_type":"academic_exam","pillar_id":None},
    # Health extended
    {"subject_id":"health_extended","subject_name":"Health and Medical Recruitment","parent_id":None,"stream":"professional","domain_type":"academic_exam","pillar_id":None},
    # International medical
    {"subject_id":"intl_medical_licensing","subject_name":"International Medical Licensing","parent_id":None,"stream":"professional","domain_type":"international","pillar_id":None},
    # IT Certifications
    {"subject_id":"cloud_certifications","subject_name":"Cloud and DevOps Certifications","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    {"subject_id":"security_certifications","subject_name":"Cybersecurity Certifications","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    {"subject_id":"project_mgmt_cert","subject_name":"Project Management Certifications","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    {"subject_id":"data_certifications","subject_name":"Data and Analytics Certifications","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    {"subject_id":"salesforce_sap_cert","subject_name":"Salesforce and SAP Certifications","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    # Agriculture
    {"subject_id":"agriculture_extended","subject_name":"Agriculture Extended Exams","parent_id":None,"stream":"govt_job","domain_type":"academic_exam","pillar_id":None},
    # B2B
    {"subject_id":"aptitude_corporate","subject_name":"Corporate Aptitude and Hiring","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    {"subject_id":"campus_placement","subject_name":"Campus Placement Preparation","parent_id":None,"stream":"skill","domain_type":"certification","pillar_id":None},
    # International licensing
    {"subject_id":"gulf_medical_licensing","subject_name":"Gulf Countries Medical Licensing","parent_id":None,"stream":"professional","domain_type":"international","pillar_id":None},
    {"subject_id":"nclex_naplex","subject_name":"NCLEX and NAPLEX US Licensing","parent_id":None,"stream":"professional","domain_type":"international","pillar_id":None},
]

print("="*60)
print("INSERTING MISSING SUBJECTS")
insert_batch("subjects", NEW_SUBJECTS, "Subjects")

# ══════════════════════════════════════════════════════════════════
# 2. MISSING TOPICS
# ══════════════════════════════════════════════════════════════════
def t(tid, sid, name, dr, visual=False, score=80, target=5000, phase="phase_1_now", order=1):
    return {"topic_id":tid,"subject_id":sid,"topic_name":name,
            "topic_name_hi":None,"topic_name_ta":None,"parent_topic_id":None,
            "difficulty_range":dr,"is_visual":visual,"coverage_score":score,
            "question_target":target,"questions_available":0,
            "display_order":order,"launch_phase":phase}

NEW_TOPICS = [
    # ── CTET and Teaching ──────────────────────────────────────────
    t("ctet_child_development_p1","ctet_teaching","CTET Paper 1: Child Development and Pedagogy","4-7",False,92,5000,"phase_1_now",1),
    t("ctet_math_science_p1","ctet_teaching","CTET Paper 1: Mathematics and Science Pedagogy","4-7",False,90,5000,"phase_1_now",2),
    t("ctet_evs_p1","ctet_teaching","CTET Paper 1: Environmental Studies (EVS)","3-6",False,88,5000,"phase_1_now",3),
    t("ctet_english_p1","ctet_teaching","CTET Paper 1: English Language and Pedagogy","3-6",False,88,5000,"phase_1_now",4),
    t("ctet_hindi_p1","ctet_teaching","CTET Paper 1: Hindi Language and Pedagogy","3-6",False,86,5000,"phase_1_now",5),
    t("ctet_child_development_p2","ctet_teaching","CTET Paper 2: Child Development and Pedagogy","5-8",False,92,5000,"phase_1_now",6),
    t("ctet_maths_p2","ctet_teaching","CTET Paper 2: Mathematics and Science (Class 6-8)","5-8",False,90,5000,"phase_1_now",7),
    t("ctet_social_studies_p2","ctet_teaching","CTET Paper 2: Social Studies and Social Science","5-8",False,88,5000,"phase_1_now",8),
    t("ctet_english_p2","ctet_teaching","CTET Paper 2: English Language Pedagogy","4-7",False,86,5000,"phase_1_now",9),
    t("teaching_pedagogy_general","child_development","Teaching Methods and Learning Theories","4-7",False,85,5000,"phase_1_now",1),
    t("child_psychology_basics","child_development","Child Psychology and Development Stages","4-7",False,85,5000,"phase_1_now",2),
    t("inclusive_education","child_development","Inclusive Education and Special Needs","4-7",False,82,5000,"phase_1_now",3),
    t("learning_disabilities","child_development","Learning Disabilities: Dyslexia, ADHD, Autism","4-7",False,80,5000,"phase_1_now",4),
    t("tn_tet_paper1","state_tet","TN TET Paper 1 (Class 1-5)","4-7",False,88,5000,"phase_1_now",1),
    t("tn_tet_paper2","state_tet","TN TET Paper 2 (Class 6-8)","5-8",False,88,5000,"phase_1_now",2),
    t("ap_tet_paper1","state_tet","AP TET Paper 1","4-7",False,85,5000,"phase_1_now",3),
    t("ts_tet_paper1","state_tet","TS TET Paper 1","4-7",False,85,5000,"phase_1_now",4),
    t("ka_tet_paper1","state_tet","Karnataka TET Paper 1","4-7",False,83,5000,"phase_1_now",5),
    t("up_tet_paper1","state_tet","UP TET Paper 1","4-7",False,88,5000,"phase_1_now",6),
    t("up_tet_paper2","state_tet","UP TET Paper 2","5-8",False,86,5000,"phase_1_now",7),
    t("bihar_tet","state_tet","Bihar STET Paper 1 and 2","4-8",False,85,5000,"phase_1_now",8),
    t("mp_tet_varg3","state_tet","MP TET Varg 3 (Primary)","4-7",False,83,5000,"phase_1_now",9),
    t("rajasthan_reet_l1","state_tet","Rajasthan REET Level 1","4-7",False,85,5000,"phase_1_now",10),
    t("rajasthan_reet_l2","state_tet","Rajasthan REET Level 2","5-8",False,85,5000,"phase_1_now",11),
    t("mh_tet_paper1","state_tet","Maharashtra TET Paper 1","4-7",False,83,5000,"phase_1_now",12),
    t("kerala_tet","state_tet","Kerala TET Paper 1 and 2","4-8",False,82,5000,"phase_1_now",13),
    t("wb_tet","state_tet","West Bengal TET Primary","4-7",False,82,5000,"phase_1_now",14),
    t("gujarat_tet","state_tet","Gujarat TET Paper 1 and 2","4-8",False,80,5000,"phase_1_now",15),
    t("punjab_tet","state_tet","Punjab TET Paper 1 and 2","4-8",False,80,5000,"phase_1_now",16),
    t("kvs_teacher","state_tet","KVS Teacher Recruitment (PGT/TGT/PRT)","5-8",False,86,5000,"phase_1_now",17),
    t("nvs_teacher","state_tet","NVS Teacher Recruitment","5-8",False,85,5000,"phase_1_now",18),
    t("dsssb_teacher","state_tet","DSSSB Delhi Teacher Recruitment","5-8",False,84,5000,"phase_1_now",19),
    t("super_tet_up","state_tet","Super TET UP Assistant Teacher","5-8",False,85,5000,"phase_1_now",20),

    # ── State Police ──────────────────────────────────────────────
    t("tn_police_si","state_police","Tamil Nadu Police SI Exam","4-7",False,88,5000,"phase_1_now",1),
    t("tn_police_constable","state_police","Tamil Nadu Police Constable Exam","3-6",False,86,5000,"phase_1_now",2),
    t("mh_police_si","state_police","Maharashtra Police SI Exam","4-7",False,86,5000,"phase_1_now",3),
    t("mh_police_constable","state_police","Maharashtra Police Constable Exam","3-6",False,85,5000,"phase_1_now",4),
    t("up_police_si","state_police","UP Police SI Exam","4-7",False,88,5000,"phase_1_now",5),
    t("up_police_constable","state_police","UP Police Constable Exam","3-6",False,88,5000,"phase_1_now",6),
    t("bihar_police_si","state_police","Bihar Police SI Exam","4-7",False,85,5000,"phase_1_now",7),
    t("karnataka_police_si","state_police","Karnataka Police SI Exam","4-7",False,84,5000,"phase_1_now",8),
    t("rajasthan_police_si","state_police","Rajasthan Police SI Exam","4-7",False,85,5000,"phase_1_now",9),
    t("mp_police_si","state_police","MP Police SI Exam","4-7",False,84,5000,"phase_1_now",10),
    t("gujarat_police_psi","state_police","Gujarat Police PSI Exam","4-7",False,83,5000,"phase_1_now",11),
    t("delhi_police_si","state_police","Delhi Police SI and Head Constable","4-7",False,87,5000,"phase_1_now",12),
    t("ap_police_si","state_police","AP Police SI Exam (SLPRB)","4-7",False,84,5000,"phase_1_now",13),
    t("telangana_police_si","state_police","Telangana Police SI Exam","4-7",False,84,5000,"phase_1_now",14),
    t("kerala_police_si","state_police","Kerala Police SI Exam","4-7",False,83,5000,"phase_1_now",15),
    t("odisha_police_si","state_police","Odisha Police SI Exam","4-7",False,82,5000,"phase_1_now",16),
    t("assam_police_si","state_police","Assam Police SI Exam","4-7",False,80,5000,"phase_1_now",17),
    t("haryana_police_si","state_police","Haryana Police SI Exam","4-7",False,83,5000,"phase_1_now",18),
    t("punjab_police_si","state_police","Punjab Police SI Exam","4-7",False,82,5000,"phase_1_now",19),
    t("wb_police_si","state_police","West Bengal Police SI Exam","4-7",False,83,5000,"phase_1_now",20),

    # ── Revenue and Civil Services ────────────────────────────────
    t("tn_vao_exam","revenue_civil","Tamil Nadu VAO (Village Administrative Officer)","4-7",False,88,5000,"phase_1_now",1),
    t("up_lekhpal","revenue_civil","UP Lekhpal Exam","3-6",False,86,5000,"phase_1_now",2),
    t("up_patwari","revenue_civil","UP Patwari and Revenue Inspector","3-6",False,85,5000,"phase_1_now",3),
    t("mp_patwari","revenue_civil","MP Patwari Exam","3-6",False,84,5000,"phase_1_now",4),
    t("rajasthan_patwari","revenue_civil","Rajasthan Patwari Exam","3-6",False,84,5000,"phase_1_now",5),
    t("punjab_patwari","revenue_civil","Punjab Patwari Exam","3-6",False,82,5000,"phase_1_now",6),
    t("haryana_patwari","revenue_civil","Haryana Patwari Exam","3-6",False,82,5000,"phase_1_now",7),
    t("karnataka_pdo","revenue_civil","Karnataka PDO (Panchayat Development Officer)","4-7",False,84,5000,"phase_1_now",8),
    t("tn_revenue_inspector","revenue_civil","TN Revenue Inspector Exam","4-7",False,85,5000,"phase_1_now",9),
    t("ap_vro_vra","revenue_civil","AP VRO/VRA Exam","3-6",False,84,5000,"phase_1_now",10),
    t("gram_panchayat_officer","revenue_civil","Gram Panchayat Officer (All States)","3-6",False,80,5000,"phase_1_now",11),
    t("tahsildar_exam","revenue_civil","Tahsildar and Deputy Tahsildar Exams","5-8",False,82,5000,"phase_1_now",12),

    # ── Banking Extended ──────────────────────────────────────────
    t("rbi_grade_b_phase1","banking_extended","RBI Grade B Phase 1 (GA+Quant+English+Reasoning)","6-9",False,90,5000,"phase_1_now",1),
    t("rbi_grade_b_phase2","banking_extended","RBI Grade B Phase 2 (Economics+Finance+Management)","7-9",False,88,5000,"phase_1_now",2),
    t("rbi_assistant","banking_extended","RBI Assistant Prelims and Mains","5-8",False,86,5000,"phase_1_now",3),
    t("sebi_grade_a","banking_extended","SEBI Grade A Officer Exam","6-9",False,86,5000,"phase_1_now",4),
    t("irdai_assistant_manager","banking_extended","IRDAI Assistant Manager Exam","5-8",False,82,5000,"phase_1_now",5),
    t("fci_manager","banking_extended","FCI Manager and Assistant Exam","5-8",False,84,5000,"phase_1_now",6),
    t("india_post_gds","banking_extended","India Post GDS and Postman Exam","3-6",False,86,5000,"phase_1_now",7),
    t("ecgc_po","banking_extended","ECGC PO Exam","5-8",False,80,5000,"phase_1_now",8),
    t("insurance_ao","banking_extended","NIACL/UIICL/Oriental Insurance AO","5-8",False,82,5000,"phase_1_now",9),
    t("esic_sso","banking_extended","ESIC SSO and MTS Exam","4-7",False,82,5000,"phase_1_now",10),
    t("coal_india_mt","banking_extended","Coal India Management Trainee","6-9",False,82,5000,"phase_1_now",11),
    t("nabard_dev_assistant","banking_extended","NABARD Development Assistant Exam","5-8",False,83,5000,"phase_1_now",12),

    # ── PSU Engineering ───────────────────────────────────────────
    t("bhel_engineer","psu_engineering","BHEL Engineer Trainee Exam","6-9",False,85,5000,"phase_1_now",1),
    t("sail_mt","psu_engineering","SAIL Management Trainee Exam","6-9",False,84,5000,"phase_1_now",2),
    t("ongc_gt","psu_engineering","ONGC Graduate Trainee Exam","6-9",False,85,5000,"phase_1_now",3),
    t("ntpc_engineer","psu_engineering","NTPC Engineer Trainee Exam","6-9",False,85,5000,"phase_1_now",4),
    t("powergrid_et","psu_engineering","Power Grid Engineer Trainee","6-9",False,84,5000,"phase_1_now",5),
    t("iocl_engineering","psu_engineering","IOCL Engineering Assistant Exam","6-9",False,84,5000,"phase_1_now",6),
    t("bpcl_officer","psu_engineering","BPCL/HPCL Officer Exam","6-9",False,83,5000,"phase_1_now",7),
    t("drdo_ceptam","psu_engineering","DRDO CEPTAM Technician and STA","5-9",False,85,5000,"phase_1_now",8),
    t("hal_design","psu_engineering","HAL Design Trainee Exam","6-9",False,83,5000,"phase_1_now",9),
    t("bel_project_engineer","psu_engineering","BEL Project Engineer Exam","6-9",False,83,5000,"phase_1_now",10),
    t("barc_scientific","psu_engineering","BARC Scientific Officer Exam","7-10",False,82,5000,"phase_1_now",11),
    t("isro_scientist","psu_engineering","ISRO Scientist and Engineer Exam","7-10",False,85,5000,"phase_1_now",12),
    t("aai_junior_executive","psu_engineering","AAI Junior Executive Exam","5-8",False,82,5000,"phase_1_now",13),
    t("gail_et","psu_engineering","GAIL Engineer Trainee Exam","6-9",False,82,5000,"phase_1_now",14),
    t("mecl_scientist","psu_engineering","MECL Scientist and Engineer","6-9",False,78,5000,"phase_1_now",15),

    # ── Agriculture Extended ──────────────────────────────────────
    t("ibps_afo","agriculture_extended","IBPS Agriculture Field Officer (AFO)","5-8",False,85,5000,"phase_1_now",1),
    t("tn_agriculture_officer","agriculture_extended","TN Agriculture Officer Exam","5-8",False,84,5000,"phase_1_now",2),
    t("up_agriculture_officer","agriculture_extended","UP Agriculture Officer Exam","5-8",False,83,5000,"phase_1_now",3),
    t("state_horticulture_officer","agriculture_extended","State Horticulture Officer Exams","5-8",False,80,5000,"phase_1_now",4),
    t("fisheries_officer","agriculture_extended","Fisheries Development Officer Exam","4-8",False,78,5000,"phase_1_now",5),
    t("veterinary_officer","agriculture_extended","Veterinary Officer State PSC Exams","5-8",False,80,5000,"phase_1_now",6),
    t("kvk_sms","agriculture_extended","KVK Subject Matter Specialist Exam","5-8",False,78,5000,"phase_1_now",7),
    t("nabard_rural_infrastructure","agriculture_extended","NABARD Rural Infrastructure and Development","5-8",False,80,5000,"phase_1_now",8),

    # ── Judicial and Legal ────────────────────────────────────────
    t("civil_judge_state","judicial_exams","Civil Judge Junior Division State PSC","6-9",False,85,5000,"phase_1_now",1),
    t("judicial_magistrate","judicial_exams","Judicial Magistrate State Exam","6-9",False,84,5000,"phase_1_now",2),
    t("district_judge_exam","judicial_exams","District Judge Lateral Entry Exam","7-10",False,82,5000,"phase_1_now",3),
    t("aibe_all_india","judicial_exams","AIBE All India Bar Examination","6-9",False,85,5000,"phase_1_now",4),
    t("cpc_crpc_evidence","judicial_exams","CPC, CrPC, Evidence Act MCQs","6-9",False,85,5000,"phase_1_now",5),
    t("constitution_bare_act","judicial_exams","Constitution of India Bare Act MCQs","5-9",False,88,5000,"phase_1_now",6),
    t("ipc_comprehensive","judicial_exams","IPC and BNS Comprehensive MCQs","6-9",False,86,5000,"phase_1_now",7),
    t("contract_law_torts","judicial_exams","Law of Contract and Torts","6-9",False,83,5000,"phase_1_now",8),
    t("family_law_india","judicial_exams","Family Law: Hindu, Muslim, Christian","6-9",False,82,5000,"phase_1_now",9),
    t("corporate_law_mca","judicial_exams","Companies Act and Corporate Law","6-9",False,82,5000,"phase_1_now",10),
    t("legislative_assembly_staff","judicial_exams","Legislative Assembly Secretariat Exams","5-8",False,78,5000,"phase_1_now",11),

    # ── Health Extended ───────────────────────────────────────────
    t("aiims_staff_nurse","health_extended","AIIMS Staff Nurse Recruitment","5-8",False,86,5000,"phase_1_now",1),
    t("esic_medical_officer","health_extended","ESIC Medical Officer Exam","6-9",False,84,5000,"phase_1_now",2),
    t("railway_medical_officer","health_extended","Railway Medical Officer Exam","6-9",False,83,5000,"phase_1_now",3),
    t("state_health_officer","health_extended","State Health Officer Recruitment","5-8",False,82,5000,"phase_1_now",4),
    t("anm_gnm_state","health_extended","ANM and GNM State Recruitment Exams","3-7",False,84,5000,"phase_1_now",5),
    t("cghs_medical_officer","health_extended","CGHS Medical Officer Exam","6-9",False,82,5000,"phase_1_now",6),
    t("dental_surgeon_state","health_extended","Dental Surgeon State PSC Exams","6-9",False,80,5000,"phase_1_now",7),
    t("paramedic_lab_technician","health_extended","Paramedic and Lab Technician Exams","4-7",False,82,5000,"phase_1_now",8),
    t("radiographer_state","health_extended","Radiographer and X-Ray Tech State Exams","4-7",False,80,5000,"phase_1_now",9),
    t("pharmacist_state","health_extended","State Pharmacist Recruitment Exams","4-7",False,82,5000,"phase_1_now",10),
    t("optometry_exam","health_extended","Optometry Licensing and State Exams","4-7",False,76,5000,"phase_1_now",11),
    t("physiotherapy_state","health_extended","Physiotherapy State Exams","4-7",False,78,5000,"phase_1_now",12),

    # ── International Medical Licensing ───────────────────────────
    t("nclex_rn_complete","nclex_naplex","NCLEX-RN Complete Preparation (US Nursing)","6-9",False,86,5000,"phase_1_now",1),
    t("nclex_pn","nclex_naplex","NCLEX-PN Practical Nurse Exam","5-8",False,82,5000,"phase_1_now",2),
    t("naplex_pharmacy","nclex_naplex","NAPLEX Pharmacy Licensing (USA)","6-9",False,80,5000,"phase_1_now",3),
    t("uae_dha_exam","gulf_medical_licensing","UAE DHA (Dubai Health Authority) Exam","6-9",False,84,5000,"phase_1_now",4),
    t("uae_haad_exam","gulf_medical_licensing","UAE HAAD (Abu Dhabi) Medical Exam","6-9",False,84,5000,"phase_1_now",5),
    t("uae_moh_exam","gulf_medical_licensing","UAE MOH Medical Licensing Exam","6-9",False,83,5000,"phase_1_now",6),
    t("saudi_scfhs","gulf_medical_licensing","Saudi SCFHS Medical Licensing","6-9",False,83,5000,"phase_1_now",7),
    t("qatar_prometric","gulf_medical_licensing","Qatar Prometric Medical Exam","6-9",False,82,5000,"phase_1_now",8),
    t("kuwait_medical","gulf_medical_licensing","Kuwait Medical Licensing Exam","6-9",False,80,5000,"phase_1_now",9),
    t("bahrain_medical","gulf_medical_licensing","Bahrain Medical Council Exam","6-9",False,78,5000,"phase_1_now",10),
    t("oman_medical","gulf_medical_licensing","Oman Medical Specialty Board Exam","6-9",False,78,5000,"phase_1_now",11),
    t("south_africa_hpcsa","intl_medical_licensing","South Africa HPCSA Medical Registration","6-9",False,76,5000,"phase_2_2027",12),
    t("australia_ahpra","intl_medical_licensing","Australia AHPRA Medical Registration","6-9",False,78,5000,"phase_1_now",13),
    t("new_zealand_mcnz","intl_medical_licensing","New Zealand MCNZ Registration","6-9",False,74,5000,"phase_2_2027",14),

    # ── Cloud Certifications ──────────────────────────────────────
    t("aws_saa_c03","cloud_certifications","AWS Solutions Architect Associate (SAA-C03)","5-8",False,92,5000,"phase_1_now",1),
    t("aws_dva_c02","cloud_certifications","AWS Developer Associate (DVA-C02)","5-8",False,88,5000,"phase_1_now",2),
    t("aws_soa_c02","cloud_certifications","AWS SysOps Administrator Associate","5-8",False,85,5000,"phase_1_now",3),
    t("aws_sap_c02","cloud_certifications","AWS Solutions Architect Professional","7-9",False,85,5000,"phase_1_now",4),
    t("aws_clf_c02","cloud_certifications","AWS Cloud Practitioner (CLF-C02)","3-6",False,90,5000,"phase_1_now",5),
    t("gcp_ace","cloud_certifications","GCP Associate Cloud Engineer","5-8",False,86,5000,"phase_1_now",6),
    t("gcp_pca","cloud_certifications","GCP Professional Cloud Architect","7-9",False,83,5000,"phase_1_now",7),
    t("gcp_pde","cloud_certifications","GCP Professional Data Engineer","6-9",False,82,5000,"phase_1_now",8),
    t("azure_az104","cloud_certifications","Azure Administrator (AZ-104)","5-8",False,88,5000,"phase_1_now",9),
    t("azure_az204","cloud_certifications","Azure Developer Associate (AZ-204)","5-8",False,85,5000,"phase_1_now",10),
    t("azure_az305","cloud_certifications","Azure Solutions Architect (AZ-305)","7-9",False,83,5000,"phase_1_now",11),
    t("azure_az900","cloud_certifications","Azure Fundamentals (AZ-900)","3-6",False,90,5000,"phase_1_now",12),
    t("cka_kubernetes","cloud_certifications","CKA Kubernetes Administrator","6-9",False,86,5000,"phase_1_now",13),
    t("ckad_kubernetes","cloud_certifications","CKAD Kubernetes Developer","6-9",False,84,5000,"phase_1_now",14),
    t("terraform_associate","cloud_certifications","HashiCorp Terraform Associate","5-8",False,84,5000,"phase_1_now",15),
    t("docker_dca","cloud_certifications","Docker Certified Associate (DCA)","5-8",False,82,5000,"phase_1_now",16),

    # ── Security Certifications ───────────────────────────────────
    t("comptia_security_plus","security_certifications","CompTIA Security+ (SY0-701)","5-8",False,90,5000,"phase_1_now",1),
    t("comptia_network_plus","security_certifications","CompTIA Network+ (N10-009)","4-7",False,86,5000,"phase_1_now",2),
    t("comptia_a_plus","security_certifications","CompTIA A+ Core 1 and Core 2","3-6",False,86,5000,"phase_1_now",3),
    t("ceh_v13","security_certifications","CEH v13 Certified Ethical Hacker","6-9",False,88,5000,"phase_1_now",4),
    t("cissp_domains","security_certifications","CISSP 8 Domains Complete","7-10",False,85,5000,"phase_1_now",5),
    t("cisa_exam","security_certifications","CISA Certified Information Systems Auditor","6-9",False,82,5000,"phase_1_now",6),
    t("cism_exam","security_certifications","CISM Certified Information Security Manager","7-9",False,80,5000,"phase_1_now",7),
    t("oscp_prep","security_certifications","OSCP Offensive Security Prep Concepts","7-10",False,80,5000,"phase_2_2027",8),
    t("ccna_200_301","security_certifications","Cisco CCNA (200-301)","5-8",False,88,5000,"phase_1_now",9),
    t("ccnp_enterprise","security_certifications","Cisco CCNP Enterprise","7-9",False,82,5000,"phase_1_now",10),

    # ── Project Management ────────────────────────────────────────
    t("pmp_pmbok7","project_mgmt_cert","PMP Project Management Professional (PMBOK 7)","6-9",False,88,5000,"phase_1_now",1),
    t("psm_scrum_master","project_mgmt_cert","PSM I Professional Scrum Master","4-7",False,85,5000,"phase_1_now",2),
    t("csm_scrum","project_mgmt_cert","CSM Certified Scrum Master","4-7",False,84,5000,"phase_1_now",3),
    t("prince2_foundation","project_mgmt_cert","PRINCE2 Foundation","5-8",False,80,5000,"phase_1_now",4),
    t("itil4_foundation","project_mgmt_cert","ITIL 4 Foundation Certification","4-7",False,82,5000,"phase_1_now",5),
    t("six_sigma_green","project_mgmt_cert","Lean Six Sigma Green Belt","5-8",False,82,5000,"phase_1_now",6),
    t("six_sigma_black","project_mgmt_cert","Lean Six Sigma Black Belt","7-9",False,78,5000,"phase_2_2027",7),
    t("pmi_acp","project_mgmt_cert","PMI-ACP Agile Certified Practitioner","5-8",False,80,5000,"phase_1_now",8),
    t("safe_agilist","project_mgmt_cert","SAFe 6 Agilist Certification","5-8",False,78,5000,"phase_1_now",9),

    # ── Data and Analytics Certifications ─────────────────────────
    t("power_bi_pl300","data_certifications","Power BI Data Analyst (PL-300)","5-8",False,88,5000,"phase_1_now",1),
    t("tableau_desktop","data_certifications","Tableau Desktop Specialist","4-7",False,85,5000,"phase_1_now",2),
    t("google_data_analytics","data_certifications","Google Data Analytics Professional Certificate","4-7",False,84,5000,"phase_1_now",3),
    t("ibm_data_science","data_certifications","IBM Data Science Professional Certificate","5-8",False,82,5000,"phase_1_now",4),
    t("databricks_associate","data_certifications","Databricks Certified Associate Developer","6-8",False,80,5000,"phase_1_now",5),
    t("snowflake_core","data_certifications","Snowflake SnowPro Core Certification","5-8",False,78,5000,"phase_1_now",6),
    t("excel_microsoft_cert","data_certifications","Microsoft Excel Expert (MO-201)","3-6",False,84,5000,"phase_1_now",7),
    t("sql_server_cert","data_certifications","Microsoft SQL Server Certification (DP-900)","4-7",False,82,5000,"phase_1_now",8),

    # ── Salesforce and SAP ────────────────────────────────────────
    t("salesforce_admin","salesforce_sap_cert","Salesforce Certified Administrator (ADM-201)","5-8",False,85,5000,"phase_1_now",1),
    t("salesforce_platform_dev","salesforce_sap_cert","Salesforce Platform Developer 1","6-8",False,82,5000,"phase_1_now",2),
    t("sap_basis_cert","salesforce_sap_cert","SAP Basis Certification (C_TADM_22)","6-8",False,78,5000,"phase_1_now",3),
    t("sap_abap_cert","salesforce_sap_cert","SAP ABAP Certification","6-8",False,76,5000,"phase_2_2027",4),
    t("servicenow_csa","salesforce_sap_cert","ServiceNow CSA Certification","4-7",False,80,5000,"phase_1_now",5),
    t("workday_hcm","salesforce_sap_cert","Workday HCM Core Certification","5-8",False,74,5000,"phase_2_2027",6),

    # ── Corporate Aptitude and Campus Placement ───────────────────
    t("tcs_nqt_prep","aptitude_corporate","TCS NQT National Qualifier Test","4-8",False,90,5000,"phase_1_now",1),
    t("infosys_sp_prep","aptitude_corporate","Infosys SP and DSE Assessment","4-8",False,88,5000,"phase_1_now",2),
    t("wipro_elite_nthp","aptitude_corporate","Wipro ELITE NTHP Assessment","4-8",False,86,5000,"phase_1_now",3),
    t("cognizant_genc","aptitude_corporate","Cognizant GenC and GenC Next","4-8",False,86,5000,"phase_1_now",4),
    t("accenture_aptitude","aptitude_corporate","Accenture Digital and Tech Aptitude","4-8",False,85,5000,"phase_1_now",5),
    t("hcl_tech_assessment","aptitude_corporate","HCL Tech Bee Assessment","4-8",False,84,5000,"phase_1_now",6),
    t("capgemini_assessment","aptitude_corporate","Capgemini Tech Assessment","4-8",False,84,5000,"phase_1_now",7),
    t("mettl_amcat_prep","aptitude_corporate","AMCAT and Mettl Assessment Prep","4-8",False,86,5000,"phase_1_now",8),
    t("campus_quant_aptitude","campus_placement","Quantitative Aptitude for Campus Placement","4-8",False,90,5000,"phase_1_now",1),
    t("campus_verbal_english","campus_placement","Verbal English for Campus Placement","3-7",False,88,5000,"phase_1_now",2),
    t("campus_logical_reasoning","campus_placement","Logical Reasoning for Campus Placement","4-8",False,88,5000,"phase_1_now",3),
    t("campus_coding_easy","campus_placement","Coding MCQs for Campus Placement (Easy)","4-7",False,88,5000,"phase_1_now",4),
    t("campus_coding_medium","campus_placement","Coding MCQs for Campus Placement (Medium)","5-8",False,86,5000,"phase_1_now",5),
    t("hr_interview_questions","campus_placement","HR Interview Questions and Answers","2-6",False,90,5000,"phase_1_now",6),
    t("group_discussion_topics","campus_placement","Group Discussion Topics and Arguments","3-7",False,85,5000,"phase_1_now",7),
    t("technical_interview_cs","campus_placement","Technical Interview: CS Fundamentals","5-9",False,88,5000,"phase_1_now",8),
]

print(f"\nTotal new topics: {len(NEW_TOPICS)}")
insert_batch("topics", NEW_TOPICS, "Topics")

# ══════════════════════════════════════════════════════════════════
# 3. MISSING EXAMS IN exam_registry
# ══════════════════════════════════════════════════════════════════
NEW_REGISTRY = []
MISSING_EXAMS = [
    # Teaching
    ("ctet_paper1","CTET Paper 1","CBSE","teaching"),
    ("ctet_paper2","CTET Paper 2","CBSE","teaching"),
    ("tn_tet","TN TET","TNPSC","state_teaching"),
    ("ap_tet","AP TET","APSC","state_teaching"),
    ("up_tet","UP TET","UPMSP","state_teaching"),
    ("bihar_stet","Bihar STET","BSEB","state_teaching"),
    ("rajasthan_reet","Rajasthan REET","BSER","state_teaching"),
    ("mp_tet","MP TET","MPPEB","state_teaching"),
    ("mh_tet","Maharashtra TET","MSCERT","state_teaching"),
    ("kvs_recruitment","KVS Teacher Recruitment","KVS","state_teaching"),
    ("nvs_recruitment","NVS Teacher Recruitment","NVS","state_teaching"),
    ("dsssb_teacher","DSSSB Teacher","DSSSB","state_teaching"),
    # State Police
    ("tn_police_si","TN Police SI","TNUSRB","state_police"),
    ("tn_police_constable","TN Police Constable","TNUSRB","state_police"),
    ("mh_police_si","Maharashtra Police SI","MPSC","state_police"),
    ("up_police_si","UP Police SI","UPPRPB","state_police"),
    ("up_police_constable","UP Police Constable","UPPRPB","state_police"),
    ("bihar_police_si","Bihar Police SI","BPSSC","state_police"),
    ("karnataka_police_si","Karnataka Police SI","KPSC","state_police"),
    ("rajasthan_police_si","Rajasthan Police SI","RPSC","state_police"),
    ("mp_police_si","MP Police SI","MPPEB","state_police"),
    ("delhi_police_si","Delhi Police SI","SSC","state_police"),
    ("ap_police_si","AP Police SI","SLPRB","state_police"),
    ("telangana_police_si","Telangana Police SI","TSLPRB","state_police"),
    # PSU
    ("bhel_et","BHEL Engineer Trainee","BHEL","psu_engineering"),
    ("sail_mt","SAIL Management Trainee","SAIL","psu_engineering"),
    ("ongc_gt","ONGC Graduate Trainee","ONGC","psu_engineering"),
    ("ntpc_et","NTPC Engineer Trainee","NTPC","psu_engineering"),
    ("isro_scientist","ISRO Scientist Engineer","ISRO","psu_engineering"),
    ("barc_oces","BARC OCES/DGFS","BARC","psu_engineering"),
    ("drdo_ceptam","DRDO CEPTAM","DRDO","psu_engineering"),
    # Banking Extended
    ("rbi_grade_b","RBI Grade B","RBI","banking"),
    ("rbi_assistant","RBI Assistant","RBI","banking"),
    ("sebi_grade_a","SEBI Grade A","SEBI","banking"),
    ("fci_exam","FCI Recruitment","FCI","central_govt_jobs"),
    ("india_post_gds","India Post GDS","India Post","central_govt_jobs"),
    ("esic_sso","ESIC SSO","ESIC","central_govt_jobs"),
    # Legal
    ("civil_judge_exam","Civil Judge State Exam","State PSC","judicial"),
    ("aibe_exam","AIBE All India Bar Exam","BCI","professional"),
    # International Medical
    ("nclex_rn","NCLEX-RN","NCSBN","international_medical"),
    ("naplex","NAPLEX Pharmacy","NABP","international_medical"),
    ("uae_dha","UAE DHA Exam","DHA","international_medical"),
    ("uae_haad","UAE HAAD Exam","HAAD","international_medical"),
    ("saudi_scfhs","Saudi SCFHS","SCFHS","international_medical"),
    ("qatar_prometric","Qatar Prometric","MOH Qatar","international_medical"),
    # Tech Certifications
    ("aws_saa","AWS Solutions Architect Associate","AWS","tech_certification"),
    ("gcp_ace","GCP Associate Cloud Engineer","Google","tech_certification"),
    ("cka","CKA Kubernetes Admin","CNCF","tech_certification"),
    ("comptia_secplus","CompTIA Security+","CompTIA","tech_certification"),
    ("ceh","CEH Certified Ethical Hacker","EC-Council","tech_certification"),
    ("cissp","CISSP","ISC2","tech_certification"),
    ("pmp","PMP Project Management","PMI","professional"),
    ("itil4","ITIL 4 Foundation","Axelos","professional"),
    ("salesforce_admin","Salesforce Admin","Salesforce","tech_certification"),
    ("power_bi_pl300","Power BI PL-300","Microsoft","tech_certification"),
    # Corporate
    ("tcs_nqt","TCS NQT","TCS","company_exams"),
    ("infosys_sp","Infosys SP Assessment","Infosys","company_exams"),
    ("wipro_elite","Wipro ELITE NTHP","Wipro","company_exams"),
    ("amcat","AMCAT Assessment","Aspiring Minds","company_exams"),
]

for exam_id, name, body, cat in MISSING_EXAMS:
    NEW_REGISTRY.append({
        "exam_id": exam_id,
        "exam_name": name,
        "conducting_body": body,
        "category": cat,
        "is_active": True,
        "research_status": "auto_imported"
    })

print(f"\nTotal new registry entries: {len(NEW_REGISTRY)}")
insert_batch("exam_registry", NEW_REGISTRY, "Exam Registry")

# ══════════════════════════════════════════════════════════════════
# 4. QUICK SYLLABUS MAP FOR NEW TOPICS
# ══════════════════════════════════════════════════════════════════
print("\nFetching updated exam registry for mapping...")
time.sleep(2)
registry = requests.get(f"{u}/rest/v1/exam_registry?select=exam_id&limit=2000",
                       headers=h, timeout=60).json()
valid_eids = set(r["exam_id"] for r in registry)

NEW_MAPS = []
# Map new topics to relevant exams
QUICK_MAP = [
    # Teaching topics → teaching exams
    (["ctet_","teaching_","child_","learning_","inclusive_","kvs_","nvs_","dsssb_","super_tet","tn_tet","ap_tet","up_tet","bihar_tet","rajasthan_reet","mh_tet","mp_tet","ka_tet","kerala_tet","wb_tet","gujarat_tet","punjab_tet"],
     ["ctet_paper1","ctet_paper2","tn_tet","ap_tet","up_tet","kvs_recruitment","nvs_recruitment","dsssb_teacher","rajasthan_reet","bihar_stet"],
     30, 1),
    # Police topics → police exams
    (["police_","vao_","patwari_","lekhpal_","pdo_","revenue_","tahsildar_","vro_","gram_panchayat_"],
     ["tn_police_si","tn_police_constable","up_police_si","up_police_constable","mh_police_si","bihar_police_si","karnataka_police_si","rajasthan_police_si","delhi_police_si"],
     35, 1),
    # PSU topics → PSU exams
    (["bhel_","sail_","ongc_","ntpc_","powergrid_","iocl_","bpcl_","drdo_","hal_","bel_","barc_","isro_","aai_","gail_","mecl_"],
     ["bhel_et","sail_mt","ongc_gt","ntpc_et","isro_scientist","barc_oces","drdo_ceptam"],
     35, 1),
    # Banking extended → banking exams
    (["rbi_grade","rbi_assist","sebi_","irdai_","fci_","india_post","ecgc_","insurance_ao","esic_sso","coal_india","nabard_dev"],
     ["rbi_grade_b","rbi_assistant","sebi_grade_a","fci_exam","india_post_gds","esic_sso"],
     35, 1),
    # Agriculture extended → agri exams
    (["ibps_afo","agriculture_officer","horticulture_officer","fisheries_","veterinary_","kvk_","nabard_rural"],
     ["ibps_afo"],
     30, 1),
    # Judicial → judicial exams
    (["civil_judge","judicial_magistrate","district_judge","aibe_","cpc_crpc","constitution_bare","ipc_comprehensive","contract_law","family_law","corporate_law","legislative_assembly"],
     ["civil_judge_exam","aibe_exam"],
     35, 1),
    # Health extended → health exams
    (["aiims_staff","esic_medical","railway_medical","state_health","anm_gnm","cghs_","dental_surgeon","paramedic_","radiographer_","pharmacist_state","optometry_","physiotherapy_"],
     ["esic_sso"],
     30, 1),
    # International medical → intl exams
    (["nclex_","naplex_","uae_dha","uae_haad","uae_moh","saudi_scfhs","qatar_prometric","kuwait_medical","bahrain_medical","oman_medical","south_africa_hpcsa","australia_ahpra","new_zealand_mcnz"],
     ["nclex_rn","naplex","uae_dha","uae_haad","saudi_scfhs","qatar_prometric"],
     40, 1),
    # Cloud certs → cloud exams
    (["aws_","gcp_","azure_","cka_","ckad_","terraform_","docker_dca"],
     ["aws_saa"],
     40, 1),
    # Security certs → security exams
    (["comptia_security","comptia_network","comptia_a_plus","ceh_","cissp_","cisa_","cism_","oscp_","ccna_","ccnp_"],
     ["comptia_secplus","ceh","cissp"],
     40, 1),
    # Project mgmt → PMP
    (["pmp_","psm_","csm_","prince2_","itil4_","six_sigma_","pmi_acp","safe_agilist"],
     ["pmp","itil4"],
     35, 1),
    # Data certs
    (["power_bi_","tableau_","google_data","ibm_data","databricks_","snowflake_","excel_microsoft","sql_server_cert"],
     ["power_bi_pl300"],
     35, 1),
    # Salesforce/SAP
    (["salesforce_","sap_","servicenow_","workday_"],
     ["salesforce_admin"],
     40, 1),
    # Campus placement
    (["tcs_nqt","infosys_sp","wipro_elite","cognizant_","accenture_","hcl_tech","capgemini_","mettl_amcat","campus_quant","campus_verbal","campus_logical","campus_coding","hr_interview","group_discussion","technical_interview"],
     ["tcs_nqt","infosys_sp","wipro_elite","amcat"],
     35, 1),
]

for topic_pats, exam_ids, weight, priority in QUICK_MAP:
    matching_topics = [
        t for t in NEW_TOPICS
        if any(pat in t["topic_id"] for pat in topic_pats)
    ]
    matching_exams = [eid for eid in exam_ids if eid in valid_eids]

    for topic in matching_topics:
        for eid in matching_exams:
            NEW_MAPS.append({
                "map_id": f"map_{uuid.uuid4().hex[:12]}",
                "exam_id": eid,
                "section_id": None,
                "topic_id": topic["topic_id"],
                "weightage_percent": weight,
                "priority": priority,
                "notes": "new_exam_auto_map"
            })

print(f"\nNew syllabus mappings: {len(NEW_MAPS)}")
insert_batch("exam_syllabus_map", NEW_MAPS, "New Syllabus Maps")

# ══════════════════════════════════════════════════════════════════
# 5. FINAL COUNT
# ══════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("FINAL COUNTS AFTER INSERT")
print("="*60)
time.sleep(2)
for label, url in [
    ("Topics", f"{u}/rest/v1/topics?select=topic_id"),
    ("Subjects", f"{u}/rest/v1/subjects?select=subject_id"),
    ("Exam Registry", f"{u}/rest/v1/exam_registry?select=exam_id"),
    ("Syllabus Maps", f"{u}/rest/v1/exam_syllabus_map?select=map_id"),
    ("Questions", f"{u}/rest/v1/questions?select=id"),
]:
    try:
        cr = requests.get(url, headers={**h,"Prefer":"count=exact","Range":"0-0"},
                         timeout=15).headers.get("content-range","?").split("/")[-1]
        print(f"  {label}: {cr}")
    except:
        print(f"  {label}: error")
