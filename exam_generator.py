#!/usr/bin/env python3
"""
exam_generator.py
-----------------
MAIN SCRIPT — Run this in GitHub Codespace.

Flow:
  1. Reads category queue in order
  2. Calls LLM (Groq/Gemini/NVIDIA rotating) to generate exam data
  3. Validates schema
  4. Inserts into Supabase
  5. Logs progress — resumable if crashed
  6. Outputs verification report for YOU to check

Usage:
    pip install -r requirements.txt
    python exam_generator.py                     # run all categories
    python exam_generator.py --phase 1           # only phase 1 (board exams)
    python exam_generator.py --category board_exams
    python exam_generator.py --subcategory CBSE
    python exam_generator.py --resume            # continue from last checkpoint
    python exam_generator.py --verify-only       # show what needs verification
"""

import os
import sys
import json
import time
import argparse
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Local modules ──
from key_rotator import key_manager
from category_queue import GENERATION_QUEUE, get_queue_by_phase, get_queue_by_category
from db_inserter import (
    insert_exam_data, log_progress, get_last_checkpoint,
    mark_for_verification, init_tracking_tables
)

# ── Config ──
API_DELAY    = float(os.getenv("API_DELAY", "1.5"))
MAX_RETRIES  = int(os.getenv("MAX_RETRIES", "3"))
BATCH_SIZE   = int(os.getenv("BATCH_SIZE", "10"))


# ══════════════════════════════════════════════════════════════
# LLM CALLER — supports Groq, Gemini, NVIDIA
# ══════════════════════════════════════════════════════════════

def call_llm(prompt: str, task: str = "bulk_generate", max_tokens: int = 4096) -> str | None:
    """
    Call the appropriate LLM based on task type.
    Handles rate limits and retries automatically.
    """
    for attempt in range(MAX_RETRIES):
        provider, key = key_manager.get_key_for_task(task)

        try:
            if provider == "groq":
                return _call_groq(key, prompt, max_tokens)
            elif provider == "gemini":
                return _call_gemini(key, prompt, max_tokens)
            elif provider == "nvidia":
                return _call_nvidia(key, prompt, max_tokens)

        except Exception as e:
            err_str = str(e).lower()

            if "rate limit" in err_str or "429" in err_str or "quota" in err_str:
                key_manager.report_rate_limit(provider, key)
                print(f"  ⚠️  Rate limit on {provider}. Retrying with different key...")
                continue

            elif "timeout" in err_str or "connection" in err_str:
                key_manager.report_error(provider, key)
                print(f"  ⚠️  Connection error on {provider}. Retry {attempt+1}/{MAX_RETRIES}")
                time.sleep(5)
                continue

            else:
                print(f"  ❌ LLM error [{provider}]: {e}")
                key_manager.report_error(provider, key)
                if attempt == MAX_RETRIES - 1:
                    return None
                time.sleep(2)
                continue

    return None


def _call_groq(api_key: str, prompt: str, max_tokens: int) -> str:
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


def _call_gemini(api_key: str, prompt: str, max_tokens: int) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.8-flash")
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            max_output_tokens=max_tokens,
            temperature=0.3,
        )
    )
    return response.text


def _call_nvidia(api_key: str, prompt: str, max_tokens: int) -> str:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key
    )
    response = client.chat.completions.create(
        model="nvidia/nemotron-3-super-120b-a12b",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content


# ══════════════════════════════════════════════════════════════
# PROMPT BUILDER
# ══════════════════════════════════════════════════════════════

def build_prompt(queue_item: dict) -> str:
    category = queue_item["category"]
    subcategory = queue_item["subcategory"]
    desc = queue_item["desc"]
    prompt_rule = queue_item.get("prompt_rule", "Generate all relevant exams.")

    return f"""You are an expert on Indian examinations and education system.

STRICT INSTRUCTION: Generate data ONLY for: {subcategory}
Description: {desc}

CRITICAL RULE: {prompt_rule}

Return ONLY a valid JSON array (no markdown, no explanation).
Each object in the array represents ONE EXAM with this exact schema. Keep the JSON as compact as possible:
[
  {{
    "exam_body": "Full name of conducting authority",
    "exam_name": "Full exam name",
    "category": "{category}",
    "subcategory": "{subcategory}",
    "state": "State code or NATIONAL",
    "frequency": "Annual",
    "mode": "Offline",
    "language_medium": ["English", "Tamil"],
    "eligibility": {{ "min_age": 18, "qualification": "10th Pass" }},
    "stages": [
      {{
        "stage_name": "Preliminary",
        "papers": [
          {{
            "paper_name": "Paper 1",
            "total_marks": 100,
            "duration_minutes": 60,
            "negative_value": 0.33,
            "subjects": [ {{ "subject_name": "Maths", "weightage_percent": 50 }} ]
          }}
        ]
      }}
    ],
    "cutoffs": {{ "general": 120 }},
    "confidence": "HIGH"
  }}
]
"""


# ══════════════════════════════════════════════════════════════
# VALIDATOR
# ══════════════════════════════════════════════════════════════

REQUIRED_FIELDS = [
    "exam_body", "exam_name", "category", "subcategory",
    "stages", "eligibility", "mode", "frequency"
]

def validate_exam_data(data: list, subcategory: str) -> tuple[list, list]:
    """Returns (valid_items, flagged_items)"""
    valid = []
    flagged = []

    for i, exam in enumerate(data):
        issues = []

        # Check required fields
        for field in REQUIRED_FIELDS:
            if field not in exam or exam[field] is None:
                issues.append(f"Missing required field: {field}")

        # Check stages exist
        if "stages" in exam:
            if not isinstance(exam["stages"], list) or len(exam["stages"]) == 0:
                issues.append("stages must be non-empty list")
            else:
                for stage in exam["stages"]:
                    if "papers" not in stage or len(stage.get("papers", [])) == 0:
                        issues.append(f"Stage '{stage.get('stage_name')}' has no papers")

        # Check confidence flag
        if exam.get("confidence") == "LOW":
            issues.append("LOW confidence — needs manual verification")

        # Add metadata
        exam["_generated_at"] = datetime.now().isoformat()
        exam["_subcategory_batch"] = subcategory
        exam["_needs_verification"] = len(issues) > 0
        exam["_issues"] = issues

        if issues:
            flagged.append(exam)
        else:
            valid.append(exam)

    return valid, flagged


# ══════════════════════════════════════════════════════════════
# PARSE JSON SAFELY
# ══════════════════════════════════════════════════════════════

def parse_json_response(raw: str) -> list | None:
    """Safely parse JSON from LLM response, handles common issues."""
    if not raw:
        return None

    # Strip markdown fences
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    # Find JSON array
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        print(f"  ⚠️  No JSON array found in response")
        return None

    json_str = cleaned[start:end+1]

    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return [data]
        return data
    except json.JSONDecodeError as e:
        print(f"  ⚠️  JSON parse error: {e}")
        # Try to salvage partial JSON
        try:
            # Find last complete object
            last_complete = json_str.rfind("},")
            if last_complete > 0:
                partial = json_str[:last_complete+1] + "]"
                return json.loads(partial)
        except Exception:
            pass
        return None


# ══════════════════════════════════════════════════════════════
# MAIN GENERATOR LOOP
# ══════════════════════════════════════════════════════════════

def process_queue_item(item: dict, dry_run: bool = False) -> dict:
    """Process one subcategory item. Returns stats dict."""
    subcategory = item["subcategory"]
    category    = item["category"]
    phase       = item["phase"]

    print(f"\n{'─'*60}")
    print(f"  📚 Phase {phase} | {category} → {subcategory}")
    print(f"  {item['desc']}")
    print(f"{'─'*60}")

    stats = {
        "subcategory": subcategory,
        "generated": 0,
        "valid": 0,
        "flagged": 0,
        "inserted": 0,
        "errors": [],
        "status": "pending"
    }

    # 1. Generate
    prompt = build_prompt(item)
    task = "detail_generate" if phase >= 9 else "bulk_generate"
    raw_response = call_llm(prompt, task=task, max_tokens=8192)

    if not raw_response:
        stats["status"] = "failed_generation"
        stats["errors"].append("LLM returned no response after all retries")
        log_progress(item, stats)
        return stats

    # 2. Parse
    exam_data = parse_json_response(raw_response)
    if not exam_data or not isinstance(exam_data, list):
        stats["status"] = "failed_parse"
        stats["errors"].append("Could not parse JSON from LLM response")
        log_progress(item, stats)
        # Save raw response for debugging
        debug_path = f"/tmp/debug_{subcategory}_{int(time.time())}.txt"
        with open(debug_path, "w") as f:
            f.write(raw_response)
        print(f"  💾 Raw response saved to {debug_path}")
        return stats

    stats["generated"] = len(exam_data)
    print(f"  ✅ Generated {len(exam_data)} exams")

    # 3. Validate
    valid_exams, flagged_exams = validate_exam_data(exam_data, subcategory)
    stats["valid"] = len(valid_exams)
    stats["flagged"] = len(flagged_exams)

    if flagged_exams:
        print(f"  ⚠️  {len(flagged_exams)} exams flagged for verification")
        for exam in flagged_exams:
            print(f"     • {exam.get('exam_name', '?')} — {exam.get('_issues', [])}")

    # 4. Insert (skip if dry run)
    if not dry_run:
        all_exams = valid_exams + flagged_exams
        inserted, insert_errors = insert_exam_data(all_exams)
        stats["inserted"] = inserted
        stats["errors"].extend(insert_errors)

        # Flag low-confidence rows for verification
        if flagged_exams:
            mark_for_verification(flagged_exams, subcategory)
    else:
        print(f"  🔵 DRY RUN — not inserting to Supabase")
        stats["inserted"] = 0

    stats["status"] = "completed"
    log_progress(item, stats)

    # 5. Rate limit delay
    time.sleep(API_DELAY)

    return stats


# ══════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="TryIT Exam Database Generator")
    parser.add_argument("--phase",       type=int,  help="Run only this phase number")
    parser.add_argument("--category",    type=str,  help="Run only this category")
    parser.add_argument("--subcategory", type=str,  help="Run only this subcategory")
    parser.add_argument("--resume",      action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--dry-run",     action="store_true", help="Generate but don't insert")
    parser.add_argument("--verify-only", action="store_true", help="Show verification queue")
    parser.add_argument("--status",      action="store_true", help="Show API key status")
    args = parser.parse_args()

    print("\n" + "═"*60)
    print("  🎓 TryIT EXAM DATABASE GENERATOR")
    print("  Building India's most comprehensive exam database")
    print("═"*60)

    if args.status:
        key_manager.print_status()
        return

    # Init tracking tables in Supabase
    init_tracking_tables()

    # Build work queue
    if args.phase:
        queue = [q for q in GENERATION_QUEUE if q["phase"] == args.phase]
    elif args.category:
        queue = [q for q in GENERATION_QUEUE if q["category"] == args.category]
    elif args.subcategory:
        queue = [q for q in GENERATION_QUEUE if q["subcategory"] == args.subcategory]
    else:
        queue = GENERATION_QUEUE

    # Resume logic — skip already completed
    if args.resume:
        last = get_last_checkpoint()
        if last:
            print(f"\n⏩ Resuming from: {last}")
            found = False
            filtered = []
            for q in queue:
                if q["subcategory"] == last:
                    found = True
                    continue
                if found:
                    filtered.append(q)
            queue = filtered
            print(f"   Remaining: {len(queue)} items\n")

    if args.verify_only:
        from db_inserter import get_verification_queue
        items = get_verification_queue()
        print(f"\n📋 VERIFICATION QUEUE ({len(items)} items):")
        for item in items:
            print(f"  • [{item.get('subcategory')}] {item.get('exam_name')} — {item.get('issues')}")
        return

    # Run stats
    total    = len(queue)
    done     = 0
    failed   = 0
    flagged  = 0

    print(f"\n📊 Queue: {total} subcategories to generate\n")

    for i, item in enumerate(queue, 1):
        print(f"\n[{i}/{total}] ", end="")
        try:
            stats = process_queue_item(item, dry_run=args.dry_run)
            done    += 1
            flagged += stats.get("flagged", 0)

            if stats["status"] == "failed_generation":
                failed += 1

        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user. Progress saved.")
            print(f"   Run with --resume to continue from: {item['subcategory']}")
            break

        except Exception as e:
            print(f"\n❌ Unexpected error on {item['subcategory']}: {e}")
            traceback.print_exc()
            failed += 1
            log_progress(item, {"status": "error", "errors": [str(e)]})
            continue

        # Print key status every 10 items
        if i % 10 == 0:
            key_manager.print_status()

    # Final summary
    print("\n" + "═"*60)
    print("  ✅ GENERATION COMPLETE")
    print(f"  Total processed : {done}")
    print(f"  Failed          : {failed}")
    print(f"  Needs review    : {flagged}")
    print(f"\n  Run: python exam_generator.py --verify-only")
    print("  to see all items needing manual verification.")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
