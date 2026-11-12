"""
fix_registry_and_map.py
Step 1: Copy all exam IDs from exams table into exam_registry
Step 2: Insert all syllabus mappings correctly
Run once — fixes the FK violation that blocked 90,283 mappings
"""
import os, requests, uuid
from dotenv import load_dotenv
from collections import defaultdict
load_dotenv()

u = os.getenv("SUPABASE_URL")
k = os.getenv("SUPABASE_KEY")
h = {
    "apikey": k,
    "Authorization": f"Bearer {k}",
    "Content-Type": "application/json",
    "Prefer": "resolution=ignore-duplicates"
}

# ── STEP 1: Fetch all exams from exams table ──────────────────────────────────
print("Fetching all exams from exams table...")
exams_raw = requests.get(
    f"{u}/rest/v1/exams?select=id,name,category&limit=1000",
    headers=h, timeout=30).json()
print(f"Found {len(exams_raw)} exams")

# ── STEP 2: Insert into exam_registry ────────────────────────────────────────
print("\nInserting into exam_registry...")
registry_rows = []
for e in exams_raw:
    registry_rows.append({
        "exam_id":           e.get("id"),
        "exam_name":         e.get("name", e.get("id","")),
        "conducting_body":   "Various",
        "category":          e.get("category","general"),
        "is_active":         True,
        "research_status":   "auto_imported",
        "notes":             f"Auto-imported from exams table category={e.get('category','')}"
    })

# Insert in batches of 100
inserted_r = skipped_r = errors_r = 0
for i in range(0, len(registry_rows), 100):
    batch = registry_rows[i:i+100]
    r = requests.post(f"{u}/rest/v1/exam_registry", headers=h, json=batch, timeout=30)
    if r.status_code in [200, 201]:
        inserted_r += len(batch)
        print(f"  Registry batch {i//100+1}: +{len(batch)} inserted")
    elif r.status_code == 409:
        skipped_r += len(batch)
        print(f"  Registry batch {i//100+1}: {len(batch)} already exist")
    else:
        errors_r += len(batch)
        print(f"  Registry batch {i//100+1}: ERROR {r.status_code}: {r.text[:100]}")

print(f"\nRegistry: {inserted_r} inserted | {skipped_r} skipped | {errors_r} errors")

# Verify
r2 = requests.get(f"{u}/rest/v1/exam_registry?select=exam_id",
    headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=10)
reg_total = r2.headers.get("content-range","?").split("/")[-1]
print(f"Total in exam_registry now: {reg_total}")

# ── STEP 3: Fetch all topics ──────────────────────────────────────────────────
print("\nFetching all topics...")
topics = requests.get(
    f"{u}/rest/v1/topics?select=topic_id,subject_id,difficulty_range&limit=2000",
    headers=h, timeout=30).json()
print(f"Found {len(topics)} topics")

# Get valid exam IDs from registry
valid_exam_ids = set(e.get("id") for e in exams_raw)

# ── EXAM DIFFICULTY MATRIX ────────────────────────────────────────────────────
EXAM_LEVEL_MAP = {
    'class_1':(1,2),'class_2':(1,3),'class_3':(2,3),'class_4':(2,4),
    'class_5':(2,4),'class_6':(3,5),'class_7':(3,5),'class_8':(4,6),
    'class_9':(4,6),'class_10':(5,7),'class_11':(5,8),'class_12':(6,8),
    'jee_main':(7,8),'jee_advanced':(8,10),'neet_ug':(7,9),'gate':(8,10),
    'cuet_ug':(5,7),'clat':(6,8),'nata':(5,7),'nift':(5,7),
    'cat':(7,9),'upsc':(7,9),'ssc_cgl':(5,7),'ssc_chsl':(4,6),
    'ssc_mts':(3,5),'ssc_gd':(3,5),'rrb_ntpc':(4,6),'rrb_group_d':(3,5),
    'rrb_je':(5,7),'ibps_po':(5,7),'ibps_clerk':(4,6),'sbi_po':(6,7),
    'sbi_clerk':(4,6),'tnpsc':(5,7),'uppsc':(6,8),'bpsc':(6,8),
    'ntse':(4,6),'nmms':(3,5),'kvpy':(6,8),'nda':(5,7),'cds':(5,7),
    'ielts':(5,7),'toefl':(5,7),'gre':(6,8),'gmat':(6,8),
    'ca_foundation':(5,7),'ca_intermediate':(6,8),'ca_final':(7,9),
    'ugc_net':(7,9),'neet_pg':(8,10),'iti':(3,6),'agniveer':(3,5),
    'jnvst':(3,5),'navodaya':(3,5),'sainik':(4,6),'aissee':(4,6),
    'olympiad':(5,8),'nso':(3,6),'imo':(3,7),'scholarship':(3,6),
    'k12_board':(2,8),'board':(2,8),
}

# ── TOPIC → EXAM RULES ───────────────────────────────────────────────────────
TOPIC_EXAM_RULES = [
    # Maths → all maths exams
    {"topic_pats":["maths","cbse_maths","data_interpretation","quantitative"],
     "exam_pats":["jee","neet","gate","ssc","rrb","ibps","sbi","upsc","tnpsc",
                  "uppsc","bpsc","ntse","kvpy","cat","cbse","icse","class_",
                  "board","scholarship","olympiad"],
     "weightage":25,"priority":1},
    # English → language exams
    {"topic_pats":["english","vocab","grammar","reading","writing"],
     "exam_pats":["ssc","rrb","ibps","sbi","upsc","ielts","toefl","clat",
                  "cuet","cbse","icse","class_","board"],
     "weightage":20,"priority":1},
    # Reasoning → competitive
    {"topic_pats":["reasoning","data_interpretation"],
     "exam_pats":["ssc","rrb","ibps","sbi","upsc","tnpsc","uppsc","bpsc",
                  "cat","ntse","clat","nda","cds"],
     "weightage":20,"priority":1},
    # GK/Current Affairs → govt exams
    {"topic_pats":["gk_","current_affairs","history","geography","polity","economy"],
     "exam_pats":["upsc","ssc","rrb","tnpsc","uppsc","bpsc","nda","cds",
                  "ibps","sbi","ntse","kvpy","cbse","class_"],
     "weightage":30,"priority":1},
    # Physics → JEE/NEET/boards
    {"topic_pats":["physics","cbse_physics"],
     "exam_pats":["jee","neet","gate","kvpy","cbse","icse","cuet","class_11",
                  "class_12","board","neet_pg"],
     "weightage":25,"priority":1},
    # Chemistry → JEE/NEET/boards
    {"topic_pats":["chemistry","cbse_chemistry"],
     "exam_pats":["jee","neet","gate","kvpy","cbse","icse","cuet",
                  "class_11","class_12","board"],
     "weightage":25,"priority":1},
    # Biology → NEET/boards
    {"topic_pats":["biology","cbse_biology"],
     "exam_pats":["neet","kvpy","cbse","icse","cuet","class_11","class_12",
                  "board","nursing","aiims","neet_pg"],
     "weightage":30,"priority":1},
    # Science general → school
    {"topic_pats":["science","cbse_science"],
     "exam_pats":["cbse","icse","class_","board","ntse","nmms","nso","olympiad"],
     "weightage":20,"priority":1},
    # SST/Social → school + competitive
    {"topic_pats":["cbse_sst","sst","social"],
     "exam_pats":["cbse","icse","class_","upsc","ssc","tnpsc"],
     "weightage":15,"priority":2},
    # Tamil → TN board + TNPSC
    {"topic_pats":["tamil","tn_state"],
     "exam_pats":["tnpsc","tn_board","tamil_nadu"],
     "weightage":35,"priority":1},
    # Telugu → AP/TS
    {"topic_pats":["telugu","ap_ts"],
     "exam_pats":["appsc","ap_","telangana","andhra"],
     "weightage":35,"priority":1},
    # Kannada → Karnataka
    {"topic_pats":["kannada","karnataka_state"],
     "exam_pats":["kpsc","karnataka","ka_"],
     "weightage":35,"priority":1},
    # Malayalam → Kerala
    {"topic_pats":["malayalam","kerala_state"],
     "exam_pats":["kerala","kl_"],
     "weightage":35,"priority":1},
    # Marathi → Maharashtra
    {"topic_pats":["marathi","mh_state"],
     "exam_pats":["mpsc","maharashtra","mh_","msbshse"],
     "weightage":35,"priority":1},
    # Hindi → UP/MP/Bihar
    {"topic_pats":["hindi","up_state","bihar_state"],
     "exam_pats":["up_board","mp_board","bihar","upsc"],
     "weightage":25,"priority":1},
    # Bengali → WB
    {"topic_pats":["bengali","wb_state"],
     "exam_pats":["wbpsc","west_bengal","wb_","madhyamik"],
     "weightage":35,"priority":1},
    # ICSE board topics
    {"topic_pats":["icse"],
     "exam_pats":["icse","isc"],
     "weightage":30,"priority":1},
    # IELTS/TOEFL/GRE → foreign exams
    {"topic_pats":["international_exams","study_abroad","ielts","toefl",
                   "french","german","gre","gmat"],
     "exam_pats":["ielts","toefl","gre","gmat","pte","sat","act"],
     "weightage":40,"priority":1},
    # Coding/DSA → tech certs + GATE CS
    {"topic_pats":["python","javascript","dsa","sql","java","cpp","html"],
     "exam_pats":["gate","aws","azure","google","tech","cuet"],
     "weightage":30,"priority":1},
    # CA/Finance → professional
    {"topic_pats":["ca_cs_cma","ca_final","finance_cert"],
     "exam_pats":["ca_foundation","ca_intermediate","ca_final","cs_executive"],
     "weightage":40,"priority":1},
    # GATE prep → GATE exams
    {"topic_pats":["gate_prep","engineering_sub","civil_eng","mechanical_eng",
                   "electrical_eng","electronics_eng"],
     "exam_pats":["gate"],
     "weightage":35,"priority":1},
    # UGC NET
    {"topic_pats":["research_academia","ugc_net"],
     "exam_pats":["ugc_net","csir"],
     "weightage":35,"priority":1},
    # Medical PG
    {"topic_pats":["medical_pg","usmle","nursing","pharmacy"],
     "exam_pats":["neet_pg","usmle","plab","fmge","nursing","aiims","norcet"],
     "weightage":35,"priority":1},
    # Defence
    {"topic_pats":["defence","nda"],
     "exam_pats":["nda","cds","afcat","agniveer","capf","rimc"],
     "weightage":25,"priority":1},
    # School scholarships
    {"topic_pats":["nep_school","foundation"],
     "exam_pats":["ntse","nmms","kvpy","nso","imo","jnvst","sainik",
                  "navodaya","aissee","olympiad","scholarship"],
     "weightage":25,"priority":1},
    # ITI/Vocational
    {"topic_pats":["iti_vocational"],
     "exam_pats":["iti"],
     "weightage":40,"priority":1},
    # State board general → respective board exams
    {"topic_pats":["cbse_maths","cbse_science","cbse_sst","cbse_physics",
                   "cbse_chemistry","cbse_biology"],
     "exam_pats":["cbse_class","cuet","jee","neet","ntse","olympiad"],
     "weightage":30,"priority":1},
]

# ── STEP 4: Build mappings using valid exam IDs ───────────────────────────────
print("\nBuilding syllabus mappings...")
mappings = []
seen = set()

for rule in TOPIC_EXAM_RULES:
    topic_pats = rule["topic_pats"]
    exam_pats  = rule["exam_pats"]
    weightage  = rule["weightage"]
    priority   = rule["priority"]

    # Find matching topics
    matching_topics = [
        t for t in topics
        if any(pat in (t.get("topic_id","") + t.get("subject_id",""))
               for pat in topic_pats)
    ]

    # Find matching exams from VALID exam IDs only
    matching_exams = [
        eid for eid in valid_exam_ids
        if any(pat in eid for pat in exam_pats)
    ]

    for topic in matching_topics:
        tid = topic["topic_id"]
        dr  = topic.get("difficulty_range","2-7")
        try: lo, hi = map(int, dr.split("-"))
        except: lo, hi = 2, 7

        for eid in matching_exams:
            # Get exam level range
            exam_lo, exam_hi = 2, 8
            for pat, levels in EXAM_LEVEL_MAP.items():
                if pat in eid:
                    exam_lo, exam_hi = levels
                    break

            # Only map if difficulty overlaps
            if lo > exam_hi or hi < exam_lo:
                continue

            key = f"{eid}_{tid}"
            if key in seen:
                continue
            seen.add(key)

            mappings.append({
                "map_id":           f"map_{uuid.uuid4().hex[:12]}",
                "exam_id":          eid,
                "section_id":       f"{eid}_main",
                "topic_id":         tid,
                "weightage_percent": weightage,
                "priority":         priority,
                "notes":            f"auto:{topic.get('subject_id','')}"
            })

print(f"Total unique mappings to insert: {len(mappings)}")

# ── STEP 5: Insert mappings in batches ────────────────────────────────────────
print("\nInserting syllabus mappings...")
inserted_m = skipped_m = errors_m = 0

for i in range(0, len(mappings), 100):
    batch = mappings[i:i+100]
    r = requests.post(f"{u}/rest/v1/exam_syllabus_map", headers=h,
                      json=batch, timeout=30)
    if r.status_code in [200, 201]:
        inserted_m += len(batch)
        if inserted_m % 1000 == 0 or i < 500:
            print(f"  Map batch {i//100+1}: +{len(batch)} (total: {inserted_m})")
    elif r.status_code == 409:
        skipped_m += len(batch)
    else:
        errors_m += len(batch)
        print(f"  Map batch {i//100+1}: ERROR {r.status_code}: {r.text[:80]}")

print(f"\nMappings: {inserted_m} inserted | {skipped_m} skipped | {errors_m} errors")

# Final count
r3 = requests.get(f"{u}/rest/v1/exam_syllabus_map?select=map_id",
    headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=10)
map_total = r3.headers.get("content-range","?").split("/")[-1]
print(f"Total mappings in DB now: {map_total}")

r4 = requests.get(f"{u}/rest/v1/exam_registry?select=exam_id",
    headers={**h,"Prefer":"count=exact","Range":"0-0"}, timeout=10)
reg_total = r4.headers.get("content-range","?").split("/")[-1]
print(f"Total in exam_registry now: {reg_total}")

print("\nDone! Now commit and push generate_master.py + hourly_report.py")
