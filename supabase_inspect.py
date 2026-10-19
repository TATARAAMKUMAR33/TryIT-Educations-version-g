#!/usr/bin/env python3
"""
supabase_inspect.py
-------------------
Run this FIRST in your GitHub Codespace to see exactly what
tables, columns, types, and row counts exist in your Supabase.

Usage:
    pip install supabase python-dotenv rich
    python supabase_inspect.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # use service role key

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
    sys.exit(1)

try:
    from supabase import create_client
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Installing dependencies...")
    os.system("pip install supabase python-dotenv rich -q")
    from supabase import create_client
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint

console = Console()
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ─────────────────────────────────────────────
# 1. List all tables via information_schema
# ─────────────────────────────────────────────
def get_all_tables():
    console.rule("[bold cyan]📋 ALL TABLES IN SUPABASE[/bold cyan]")
    try:
        result = supabase.rpc("get_tables_info", {}).execute()
        # Fallback: use raw SQL via postgrest
    except Exception:
        pass

    # Direct query via information_schema
    query = """
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """
    try:
        result = supabase.rpc("exec_sql", {"sql": query}).execute()
        tables = result.data
    except Exception:
        # Fallback: try listing known tables by attempting empty selects
        console.print("[yellow]⚠ RPC not available — using direct table probe[/yellow]")
        tables = probe_tables_direct()
        return tables

    table = Table(title="Public Schema Tables", show_lines=True)
    table.add_column("Table Name", style="cyan")
    table.add_column("Type", style="green")

    for row in tables:
        table.add_row(row.get("table_name", ""), row.get("table_type", ""))

    console.print(table)
    return [r["table_name"] for r in tables]


# ─────────────────────────────────────────────
# 2. Probe tables directly (most reliable)
# ─────────────────────────────────────────────
COMMON_EXAM_TABLES = [
    # Core exam tables
    "exams", "exam_bodies", "exam_categories", "exam_stages",
    "exam_papers", "exam_syllabus", "exam_topics", "exam_subtopics",
    "exam_pattern", "exam_eligibility", "exam_cutoffs",
    "exam_schedule", "exam_results",
    # Domain tables
    "states", "boards", "universities", "courses",
    "subjects", "departments",
    # Job exam tables
    "psc_exams", "central_exams", "departmental_exams",
    "military_exams", "police_exams", "banking_exams",
    # Education tables
    "school_exams", "board_exams", "entrance_exams",
    "scholarship_exams", "pg_exams", "phd_exams",
    # Certification tables
    "skill_exams", "certification_exams", "tech_certifications",
    "language_exams", "foreign_exams",
    # Progress tracking
    "generation_log", "generation_progress", "verification_queue",
    # NEP/PARAKH
    "nep_assessments", "parakh_assessments",
]

def probe_tables_direct():
    """Try selecting 1 row from each known table name to detect existence."""
    found = []
    not_found = []

    console.print("\n[bold]🔍 Probing known table names...[/bold]\n")

    for tname in COMMON_EXAM_TABLES:
        try:
            res = supabase.table(tname).select("*").limit(1).execute()
            row_count = get_row_count(tname)
            found.append({"table": tname, "rows": row_count, "status": "✅"})
        except Exception as e:
            err = str(e).lower()
            if "does not exist" in err or "42p01" in err or "relation" in err:
                not_found.append(tname)
            else:
                found.append({"table": tname, "rows": "?", "status": "⚠️ " + str(e)[:40]})

    return found, not_found


def get_row_count(table_name):
    try:
        res = supabase.table(table_name).select("*", count="exact").limit(0).execute()
        return res.count if res.count is not None else "?"
    except Exception:
        return "?"


# ─────────────────────────────────────────────
# 3. Get columns for a specific table
# ─────────────────────────────────────────────
def get_table_columns(table_name):
    try:
        res = supabase.table(table_name).select("*").limit(1).execute()
        if res.data:
            return list(res.data[0].keys())
        else:
            return ["(table exists but empty — no columns visible)"]
    except Exception as e:
        return [f"Error: {e}"]


# ─────────────────────────────────────────────
# 4. MAIN INSPECT ROUTINE
# ─────────────────────────────────────────────
def main():
    console.print("\n[bold magenta]═══════════════════════════════════════════════[/bold magenta]")
    console.print("[bold magenta]   SUPABASE INSPECTOR — TryIT Exam Database   [/bold magenta]")
    console.print("[bold magenta]═══════════════════════════════════════════════[/bold magenta]\n")

    console.print(f"[green]✅ Connected to:[/green] {SUPABASE_URL}\n")

    # Probe tables
    found, not_found = probe_tables_direct()

    # ── FOUND TABLES ──
    if found:
        t = Table(title="✅ Tables Found in Supabase", show_lines=True, style="green")
        t.add_column("Table Name", style="cyan", min_width=30)
        t.add_column("Row Count", style="yellow", justify="right")
        t.add_column("Status", style="green")
        t.add_column("Columns", style="white")

        for row in found:
            cols = get_table_columns(row["table"])
            col_str = ", ".join(cols[:8])
            if len(cols) > 8:
                col_str += f" ... +{len(cols)-8} more"
            t.add_row(
                row["table"],
                str(row["rows"]),
                row["status"],
                col_str
            )
        console.print(t)

    # ── MISSING TABLES ──
    if not_found:
        console.print(f"\n[bold red]❌ Tables NOT found ({len(not_found)}):[/bold red]")
        for tn in not_found:
            console.print(f"   [red]✗[/red] {tn}")

    # ── SUMMARY ──
    console.print(f"\n[bold]📊 SUMMARY[/bold]")
    console.print(f"   Tables found    : [green]{len(found)}[/green]")
    console.print(f"   Tables missing  : [red]{len(not_found)}[/red]")
    console.print(f"   Total probed    : {len(COMMON_EXAM_TABLES)}")

    # ── COLUMN DETAIL for found tables ──
    if found:
        console.print("\n[bold cyan]📐 DETAILED COLUMN VIEW (found tables)[/bold cyan]\n")
        for row in found:
            if "✅" in row["status"]:
                cols = get_table_columns(row["table"])
                console.print(f"[cyan]{row['table']}[/cyan] ({row['rows']} rows)")
                console.print(f"  Columns: [yellow]{', '.join(cols)}[/yellow]\n")

    # ── WHAT'S NEEDED ──
    console.rule("[bold]📋 TABLES NEEDED FOR EXAM GENERATOR[/bold]")
    needed = {
        "exam_bodies": "WHO conducts the exam (UPSC, TNPSC, CBSE...)",
        "exam_categories": "Board/Entrance/Job/Certification/Military...",
        "exams": "Each exam (IAS, JEE Main, NEET, TNPSC Gr2...)",
        "exam_stages": "Prelims/Mains/Tier1/Tier2/Interview/PT/Medical...",
        "exam_papers": "Each paper within a stage (Paper1, GS1, Maths...)",
        "exam_syllabus": "Topic-wise syllabus per paper",
        "exam_topics": "Individual topics with weightage",
        "exam_pattern": "MCQ/Descriptive/Coding/Physical — marks, duration",
        "exam_eligibility": "Age/qualification/domicile/attempts/physical",
        "exam_cutoffs": "Category-wise historical cutoffs",
        "generation_log": "Script progress tracking",
        "generation_progress": "Resume from checkpoint",
        "verification_queue": "Rows YOU need to manually verify",
    }
    for tname, desc in needed.items():
        exists = any(r["table"] == tname for r in found if "✅" in r["status"])
        icon = "✅" if exists else "❌ MISSING"
        console.print(f"  {icon}  [cyan]{tname}[/cyan] — {desc}")

    console.print("\n[bold yellow]👆 Share this output with Claude to proceed![/bold yellow]\n")


if __name__ == "__main__":
    main()
