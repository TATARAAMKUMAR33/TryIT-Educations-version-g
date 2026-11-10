"""
build_syllabus_map.py
Connects all 500 exams to relevant topics with weightage and difficulty.
Run once to populate exam_syllabus_map table.
"""
import os, requests, uuid
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

# ── EXAM DIFFICULTY MATRIX ────────────────────────────────────────────────────
# Maps exam_id patterns to their tier difficulty ranges
EXAM_LEVEL_MAP = {
    # School boards by class
    'class_1': (1,2), 'class_2': (1,3), 'class_3': (2,3),
    'class_4': (2,4), 'class_5': (2,4), 'class_6': (3,5),
    'class_7': (3,5), 'class_8': (4,6), 'class_9': (4,6),
    'class_10': (5,7), 'class_11': (5,8), 'class_12': (6,8),
    # Entrance exams
    'jee_main': (7,8), 'jee_advanced': (8,10), 'neet_ug': (7,9),
    'gate': (8,10), 'cuet_ug': (5,7), 'cuet_pg': (6,8),
    'clat': (6,8), 'nata': (5,7), 'nift': (5,7), 'nid': (5,7),
    'cat': (7,9), 'mat': (5,7), 'xat': (6,8), 'snap': (5,7),
    'nmat': (5,7), 'cmat': (5,7), 'iit_jam': (7,9),
    # Govt exams
    'upsc_cse': (7,9), 'upsc': (7,9),
    'ssc_cgl': (5,7), 'ssc_chsl': (4,6), 'ssc_mts': (3,5),
    'ssc_gd': (3,5), 'ssc': (4,6),
    'rrb_ntpc': (4,6), 'rrb_group_d': (3,5), 'rrb_je': (5,7),
    'ibps_po': (5,7), 'ibps_clerk': (4,6), 'sbi_po': (6,7),
    'sbi_clerk': (4,6), 'lic': (5,7), 'nabard': (5,7),
    'nda': (5,7), 'cds': (5,7), 'afcat': (5,7), 'agniveer': (3,5),
    'capf': (6,8),
    # State PSC
    'tnpsc': (5,7), 'uppsc': (6,8), 'bpsc': (6,8),
    'mpsc': (6,8), 'kpsc': (6,8), 'appsc': (6,8),
    'wbpsc': (6,8), 'rpsc': (6,8), 'gpsc': (6,8), 'ppsc': (6,8),
    # Scholarship
    'ntse': (4,6), 'kvpy': (6,8), 'nmms': (3,5),
    'olympiad': (5,8), 'nso': (3,6), 'imo': (3,7),
    'jnvst': (3,5), 'sainik': (4,6), 'navodaya': (3,5),
    # Professional
    'ca_foundation': (5,7), 'ca_intermediate': (6,8), 'ca_final': (7,9),
    'cs': (6,8), 'cma': (6,8),
    'ugc_net': (7,9), 'csir': (7,9),
    # Foreign/Language
    'ielts': (5,7), 'toefl': (5,7), 'pte': (5,7), 'gre': (6,8),
    'gmat': (6,8), 'sat': (5,7), 'act': (5,7),
    # Tech
    'aws': (5,7), 'azure': (5,7), 'google': (5,7),
    # Medical
    'neet_pg': (8,10), 'usmle': (8,10), 'plab': (7,9), 'fmge': (7,9),
    # ITI/Vocational
    'iti': (3,6),
}

# ── TOPIC TO EXAM SUBJECT MAPPING ─────────────────────────────────────────────
# Which topic subjects map to which exam categories
TOPIC_EXAM_RULES = [
    # Maths topics → all maths-based exams
    {
        'topic_subjects': ['maths_arithmetic','maths_algebra','maths_geometry',
                          'maths_trigonometry','maths_stats','maths_calculus',
                          'cbse_maths','data_interpretation'],
        'exam_patterns': ['jee','neet','gate','ssc','rrb','ibps','sbi','upsc',
                         'tnpsc','uppsc','bpsc','ntse','kvpy','nmms','cat',
                         'cbse','icse','tn_state','mh_state','karnataka',
                         'up_state','gujarat','wb_state','class_'],
        'weightage': 25,
        'priority': 1
    },
    # English topics → language-based exams
    {
        'topic_subjects': ['english','english_grammar','english_vocab',
                          'english_reading','english_writing'],
        'exam_patterns': ['ssc','rrb','ibps','sbi','upsc','ielts','toefl',
                         'pte','gre','gmat','clat','cuet','cbse','icse',
                         'tnpsc','class_'],
        'weightage': 20,
        'priority': 1
    },
    # Reasoning → competitive exams
    {
        'topic_subjects': ['reasoning_verbal','reasoning_nonverbal',
                          'reasoning_critical','data_interpretation'],
        'exam_patterns': ['ssc','rrb','ibps','sbi','upsc','tnpsc','uppsc',
                         'bpsc','cat','ntse','clat'],
        'weightage': 20,
        'priority': 1
    },
    # GK/Current Affairs → all govt exams
    {
        'topic_subjects': ['gk_history','gk_geography','gk_polity','gk_economy',
                          'gk_science','gk_sports','gk_india','gk_awards',
                          'current_affairs','current_affairs_full'],
        'exam_patterns': ['upsc','ssc','rrb','tnpsc','uppsc','bpsc','mpsc',
                         'kpsc','appsc','nda','cds','ibps','sbi'],
        'weightage': 30,
        'priority': 1
    },
    # Physics → JEE/NEET/GATE/Class 11-12
    {
        'topic_subjects': ['physics','cbse_physics_11_12'],
        'exam_patterns': ['jee','neet','gate','kvpy','cbse','icse','neet_pg',
                         'cuet','class_11','class_12'],
        'weightage': 25,
        'priority': 1
    },
    # Chemistry → JEE/NEET/Class 11-12
    {
        'topic_subjects': ['chemistry','cbse_chemistry_11_12'],
        'exam_patterns': ['jee','neet','gate','kvpy','cbse','icse',
                         'cuet','class_11','class_12'],
        'weightage': 25,
        'priority': 1
    },
    # Biology → NEET/Class 11-12
    {
        'topic_subjects': ['biology','cbse_biology_11_12'],
        'exam_patterns': ['neet','kvpy','cbse','icse','cuet',
                         'class_11','class_12','nursing','aiims'],
        'weightage': 30,
        'priority': 1
    },
    # Science general → School exams
    {
        'topic_subjects': ['science_gen','cbse_science'],
        'exam_patterns': ['cbse','icse','ntse','nmms','nso','class_6',
                         'class_7','class_8','class_9','class_10',
                         'tn_state','mh_state','karnataka','up_state'],
        'weightage': 20,
        'priority': 1
    },
    # Social Studies/SST → School + Competitive
    {
        'topic_subjects': ['cbse_sst','history','geography','polity','economy'],
        'exam_patterns': ['cbse','icse','class_6','class_7','class_8',
                         'class_9','class_10','upsc','ssc','tnpsc'],
        'weightage': 15,
        'priority': 2
    },
    # Tamil → TN board + TNPSC
    {
        'topic_subjects': ['tamil_full','tn_state_board'],
        'exam_patterns': ['tnpsc','tamil_nadu','tn_'],
        'weightage': 35,
        'priority': 1
    },
    # Telugu → AP/TS board + APPSC
    {
        'topic_subjects': ['telugu_full','ap_ts_state_board'],
        'exam_patterns': ['appsc','andhra_pradesh','ap_','telangana'],
        'weightage': 35,
        'priority': 1
    },
    # Kannada → Karnataka board + KPSC
    {
        'topic_subjects': ['kannada_full','karnataka_state_board'],
        'exam_patterns': ['kpsc','karnataka','ka_'],
        'weightage': 35,
        'priority': 1
    },
    # Malayalam → Kerala board + Kerala PSC
    {
        'topic_subjects': ['malayalam_full','kerala_state_board'],
        'exam_patterns': ['kerala','kl_'],
        'weightage': 35,
        'priority': 1
    },
    # Marathi → MH board + MPSC
    {
        'topic_subjects': ['marathi_full','mh_state_board'],
        'exam_patterns': ['mpsc','maharashtra','mh_'],
        'weightage': 35,
        'priority': 1
    },
    # Hindi → UP/MP/Bihar boards + UPSC Hindi medium
    {
        'topic_subjects': ['hindi_language','up_state_board','bihar_state_board'],
        'exam_patterns': ['up_board','mp_board','bihar','hindi','upsc'],
        'weightage': 25,
        'priority': 1
    },
    # Bengali → WB board + WBPSC
    {
        'topic_subjects': ['bengali_full','wb_state_board'],
        'exam_patterns': ['wbpsc','west_bengal','wb_'],
        'weightage': 35,
        'priority': 1
    },
    # Gujarati → Gujarat board + GPSC
    {
        'topic_subjects': ['gujarati_full','gujarat_state_board'],
        'exam_patterns': ['gpsc','gujarat','gj_'],
        'weightage': 35,
        'priority': 1
    },
    # Punjabi → Punjab board + PPSC
    {
        'topic_subjects': ['punjabi_full','punjab_state_board'],
        'exam_patterns': ['ppsc','punjab','pb_'],
        'weightage': 35,
        'priority': 1
    },
    # IELTS/TOEFL/GRE → foreign language exams
    {
        'topic_subjects': ['international_exams','study_abroad_usa','study_abroad_uk',
                          'study_abroad_canada','study_abroad_australia',
                          'french_language','german_language'],
        'exam_patterns': ['ielts','toefl','pte','gre','gmat','sat'],
        'weightage': 40,
        'priority': 1
    },
    # Coding/DSA → Tech certifications + GATE CS
    {
        'topic_subjects': ['python_programming','javascript_programming',
                          'dsa_algorithms','sql_database','java_programming'],
        'exam_patterns': ['gate','aws','azure','google','tech'],
        'weightage': 30,
        'priority': 1
    },
    # CA/Finance → Professional exams
    {
        'topic_subjects': ['ca_cs_cma','ca_final','finance_certifications'],
        'exam_patterns': ['ca_foundation','ca_intermediate','ca_final','cs'],
        'weightage': 40,
        'priority': 1
    },
    # UG Entrances
    {
        'topic_subjects': ['ug_pg_entrances'],
        'exam_patterns': ['jee','neet','clat','nata','nift','cuet','ipmat'],
        'weightage': 30,
        'priority': 1
    },
    # GATE prep
    {
        'topic_subjects': ['gate_prep','engineering_sub','civil_engineering',
                          'mechanical_engineering','electrical_engineering',
                          'electronics_engineering'],
        'exam_patterns': ['gate'],
        'weightage': 35,
        'priority': 1
    },
    # NTSE/Scholarship
    {
        'topic_subjects': ['nep_school_foundation'],
        'exam_patterns': ['ntse','nmms','kvpy','nso','imo','jnvst','sainik',
                         'navodaya','olympiad'],
        'weightage': 25,
        'priority': 1
    },
    # Medical PG
    {
        'topic_subjects': ['medical_pg','usmle_prep','nursing','pharmacy'],
        'exam_patterns': ['neet_pg','usmle','plab','fmge','nursing','aiims'],
        'weightage': 35,
        'priority': 1
    },
    # UGC NET
    {
        'topic_subjects': ['research_academia'],
        'exam_patterns': ['ugc_net','csir'],
        'weightage': 35,
        'priority': 1
    },
    # Defence
    {
        'topic_subjects': ['defence_exams','nep_school_foundation'],
        'exam_patterns': ['nda','cds','afcat','agniveer','capf','rimc'],
        'weightage': 25,
        'priority': 1
    },
    # ITI/Vocational
    {
        'topic_subjects': ['iti_vocational'],
        'exam_patterns': ['iti'],
        'weightage': 40,
        'priority': 1
    },
]

# ── FETCH ALL EXAMS AND TOPICS ────────────────────────────────────────────────
print("Fetching exams and topics...")
exams = requests.get(f'{u}/rest/v1/exams?select=id,category&limit=1000', headers=h).json()
topics = requests.get(f'{u}/rest/v1/topics?select=topic_id,subject_id,difficulty_range&limit=2000', headers=h).json()

print(f"Exams: {len(exams)} | Topics: {len(topics)}")

# ── BUILD MAPPINGS ────────────────────────────────────────────────────────────
mappings = []

for rule in TOPIC_EXAM_RULES:
    topic_subs = rule['topic_subjects']
    exam_pats = rule['exam_patterns']
    weightage = rule['weightage']
    priority = rule['priority']

    # Find matching topics
    matching_topics = [
        t for t in topics
        if any(sub in (t.get('subject_id') or '') for sub in topic_subs)
    ]

    # Find matching exams
    matching_exams = [
        e for e in exams
        if any(pat in (e.get('id') or '') for pat in exam_pats)
    ]

    for topic in matching_topics:
        for exam in matching_exams:
            # Get difficulty range
            dr = topic.get('difficulty_range', '2-7')
            try:
                lo, hi = map(int, dr.split('-'))
            except:
                lo, hi = 2, 7

            # Get exam level range
            exam_id = exam.get('id', '')
            exam_lo, exam_hi = 3, 7  # default
            for pat, levels in EXAM_LEVEL_MAP.items():
                if pat in exam_id:
                    exam_lo, exam_hi = levels
                    break

            # Only map if topic difficulty overlaps with exam difficulty
            if lo <= exam_hi and hi >= exam_lo:
                mappings.append({
                    'map_id': f'map_{uuid.uuid4().hex[:12]}',
                    'exam_id': exam_id,
                    'section_id': f"{exam_id}_main",
                    'topic_id': topic['topic_id'],
                    'weightage_percent': weightage,
                    'priority': priority,
                    'notes': f'Auto-mapped: {topic["subject_id"]} → {exam.get("category","")}'
                })

print(f"\nTotal mappings to insert: {len(mappings)}")

# Remove duplicates by exam_id+topic_id
seen = set()
unique_mappings = []
for m in mappings:
    key = f"{m['exam_id']}_{m['topic_id']}"
    if key not in seen:
        seen.add(key)
        unique_mappings.append(m)

print(f"Unique mappings: {len(unique_mappings)}")

# ── INSERT IN BATCHES ─────────────────────────────────────────────────────────
BATCH = 100
inserted = skipped = errors = 0

for i in range(0, len(unique_mappings), BATCH):
    batch = unique_mappings[i:i+BATCH]
    r = requests.post(f'{u}/rest/v1/exam_syllabus_map', headers=h, json=batch, timeout=30)
    if r.status_code in [200, 201]:
        inserted += len(batch)
        print(f'Batch {i//BATCH+1}: +{len(batch)} inserted (total: {inserted})')
    elif r.status_code == 409:
        skipped += len(batch)
        print(f'Batch {i//BATCH+1}: {len(batch)} already exist')
    else:
        errors += len(batch)
        print(f'Batch {i//BATCH+1}: ERROR {r.status_code}: {r.text[:100]}')

print(f'\nDONE: {inserted} inserted | {skipped} skipped | {errors} errors')

# Verify
r2 = requests.get(f'{u}/rest/v1/exam_syllabus_map?select=exam_id',
    headers={**h,'Prefer':'count=exact','Range':'0-0'}, timeout=10)
total = r2.headers.get('content-range','?').split('/')[-1]
print(f'Total mappings in DB now: {total}')
