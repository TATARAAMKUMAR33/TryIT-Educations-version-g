"""
db_inserter.py — adapted to TryIT existing schema
"""
import os
import re
import json
from datetime import datetime
from dotenv import load_dotenv

# 🚨 Explicitly tell it to look for the .env file in the current directory
load_dotenv(dotenv_path=".env")

_supabase = None

def get_supabase():
    global _supabase
    if _supabase is None:
        from supabase import create_client
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not url or not key:
            raise RuntimeError(f"❌ Missing credentials. URL: {bool(url)}, KEY: {bool(key)}. Check your .env file.")
            
        _supabase = create_client(url, key)
    return _supabase

def make_slug(name: str, subcategory: str) -> str:
    base = f"{name}_{subcategory}".lower()
    base = re.sub(r'[^a-z0-9\s]', '', base)
    base = re.sub(r'\s+', '_', base.strip())
    base = base[:50]
    return base

ELIGIBILITY_LEVEL_MAP = {
    "class 1": 1, "class 2": 1, "class 3": 1, "class 4": 1, "class 5": 1, "primary": 1,
    "class 6": 2, "class 7": 2, "class 8": 2, "class 9": 2, "class 10": 2, "10th": 2, "sslc": 2, "matriculation": 2,
    "class 11": 3, "class 12": 3, "12th": 3, "+2": 3, "hsc": 3, "intermediate": 3, "puc": 3,
    "graduate": 4, "ug": 4, "degree": 4, "bachelor": 4,
    "pg": 5, "post graduate": 5, "master": 5, "mba": 5, "mtech": 5,
    "phd": 6, "doctorate": 6,
}

def get_eligibility_level(eligibility_str: str) -> int:
    if not eligibility_str: return 4
    lower = eligibility_str.lower()
    for key, level in ELIGIBILITY_LEVEL_MAP.items():
        if key in lower: return level
    return 4

def map_to_schema(exam: dict, subcategory: str) -> dict:
    tiers = []
    stages = exam.get("stages", [])
    
    if stages:
        for stage in stages:
            stage_name = stage.get("stage_name", stage.get("stage_short", ""))
            papers = stage.get("papers", [])
            for paper in papers:
                tier_entry = {
                    "tier": f"{stage_name} - {paper.get('paper_name', '')}" if len(papers) > 1 else stage_name,
                    "q": paper.get("questions", 0),
                    "time": paper.get("duration_minutes", 0),
                    "marks": paper.get("total_marks", 0),
                }
                subjects = paper.get("subjects", [])
                if subjects:
                    tier_entry["subjects"] = [
                        {"name": s.get("subject_name", ""), "weightage": s.get("weightage_percent", 0), "topics": s.get("key_topics", []), "difficulty": s.get("difficulty", "Moderate")}
                        for s in subjects
                    ]
                tiers.append(tier_entry)
    else:
        tiers = [{"tier": "Written Test", "q": 0, "time": 0, "marks": 0}]

    has_negative = False
    neg_value = 0
    for stage in stages:
        for paper in stage.get("papers", []):
            if paper.get("negative_marking"):
                has_negative = True
                neg_value = paper.get("negative_value", 0.25)
                break

    elig = exam.get("eligibility", {})
    elig_qual = elig.get("qualification", "") if isinstance(elig, dict) else str(elig)
    
    lang = exam.get("language_medium", ["English"])
    if isinstance(lang, str): lang = [lang]

    state_val = exam.get("state", "NATIONAL") or "NATIONAL"

    return {
        "id":                 make_slug(exam.get("exam_name", "unknown"), subcategory),
        "name":               exam.get("exam_name", ""),
        "short_name":         exam.get("exam_name_short", ""),
        "conducting_body":    exam.get("exam_body", ""),
        "exam_body_short":    exam.get("exam_body_short", ""),
        "category":           exam.get("category", subcategory),
        "subcategory":        exam.get("subcategory", subcategory),
        "eligibility_level":  get_eligibility_level(elig_qual),
        "eligibility":        elig if isinstance(elig, dict) else {"qualification": elig_qual},
        "tiers":              tiers,
        "total_vacancies":    exam.get("vacancy_approx"),
        "frequency":          exam.get("frequency", "Annual").lower(),
        "official_website":   exam.get("official_website"),
        "negative_marking":   has_negative,
        "state_specific":     state_val if state_val != "NATIONAL" else None,
        "state":              state_val,
        "language_medium":    lang if isinstance(lang, list) else [lang] if lang else ["English"],
        "mode":               exam.get("mode", "Offline"),
        "cutoffs":            exam.get("cutoffs"),
        "difficulty":         exam.get("difficulty", "Moderate"),
        "notes":              exam.get("notes"),
        "confidence":         exam.get("confidence", "HIGH"),
        "needs_verification": exam.get("_needs_verification", False),
        "notification_month": exam.get("notification_month"),
        "exam_month":         exam.get("exam_month"),
        "generated_at":       datetime.now().isoformat(),
    }

def init_tracking_tables():
    sb = get_supabase()
    try:
        sb.table("exams").select("id").limit(1).execute()
        sb.table("generation_log").select("*").limit(1).execute()
        sb.table("generation_progress").select("*").limit(1).execute()
        sb.table("verification_queue").select("*").limit(1).execute()
        print("✅ All Supabase tables verified")
    except Exception as e:
        print(f"⚠️ Table check warning: {e}")

def insert_exam_data(exams: list) -> tuple[int, list]:
    sb = get_supabase()
    inserted, errors = 0, []
    for exam in exams:
        try:
            row = map_to_schema(exam, exam.get("subcategory", ""))
            if not row["name"]: continue
            result = sb.table("exams").upsert(row, on_conflict="name,subcategory").execute()
            if result.data:
                inserted += 1
                print(f"    💾 Saved: {row['name']}")
        except Exception as e:
            print(f"    ❌ Failed: {exam.get('exam_name', '?')} — {str(e)[:80]}")
            errors.append(str(e))
    print(f"\n  ✅ Inserted {inserted}/{len(exams)} to Supabase")
    return inserted, errors

def log_progress(queue_item: dict, stats: dict):
    sb = get_supabase()
    try:
        sb.table("generation_log").insert({
            "subcategory": queue_item["subcategory"], "category": queue_item["category"],
            "phase": queue_item["phase"], "status": stats.get("status", "unknown"),
            "generated_count": stats.get("generated", 0), "valid_count": stats.get("valid", 0),
            "flagged_count": stats.get("flagged", 0), "inserted_count": stats.get("inserted", 0),
            "errors": stats.get("errors", []),
        }).execute()
        sb.table("generation_progress").upsert({
            "id": 1, "last_subcategory": queue_item["subcategory"],
            "last_category": queue_item["category"], "last_phase": queue_item["phase"],
            "updated_at": datetime.now().isoformat(),
        }).execute()
    except Exception: pass

def get_last_checkpoint() -> str | None:
    try:
        result = get_supabase().table("generation_progress").select("last_subcategory").eq("id", 1).execute()
        if result.data: return result.data[0]["last_subcategory"]
    except Exception: pass
    return None

def mark_for_verification(exams: list, subcategory: str):
    sb = get_supabase()
    for exam in exams:
        try:
            sb.table("verification_queue").insert({
                "exam_name": exam.get("exam_name", "Unknown"), "subcategory": subcategory,
                "category": exam.get("category", ""), "issues": exam.get("_issues", []),
                "exam_data": {k: v for k, v in exam.items() if not k.startswith("_")},
                "verified": False,
            }).execute()
        except Exception: pass

def get_verification_queue() -> list:
    try:
        return get_supabase().table("verification_queue").select("*").eq("verified", False).execute().data or []
    except Exception: return []
