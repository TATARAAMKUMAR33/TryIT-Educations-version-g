#!/usr/bin/env python3
"""
audit_and_fix.py
----------------
Permanent script — run anytime to:
1. Show full audit of what's in Supabase
2. Find gaps — what's missing vs master list
3. Find duplicates — same name saved twice
4. Find thin entries — exams with too few tiers
5. Auto-fix gaps by regenerating missing ones

Usage:
    python audit_and_fix.py              # full audit report
    python audit_and_fix.py --fix        # fix all gaps automatically
    python audit_and_fix.py --duplicates # show and remove duplicates
    python audit_and_fix.py --thin       # show thin entries (< 2 tiers)
"""

import os
import sys
import json
import argparse
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv()

# ── Master exam list — EVERY exam that should exist ──────────────
# This is the ground truth. Add to this list as we expand coverage.

MASTER_EXAM_LIST = {

    # ── BOARD EXAMS ──────────────────────────────────────────────
    "CBSE_1_6":   {"expected_min": 6,  "category": "board_exams",        "desc": "CBSE Class 1-6"},
    "CBSE_7_12":  {"expected_min": 6,  "category": "board_exams",        "desc": "CBSE Class 7-12"},
    "ICSE_1_6":   {"expected_min": 6,  "category": "board_exams",        "desc": "ICSE Class 1-6"},
    "ICSE_7_12":  {"expected_min": 6,  "category": "board_exams",        "desc": "ICSE Class 7-12"},
    "NIOS_1_6":   {"expected_min": 6,  "category": "board_exams",        "desc": "NIOS Class 1-6"},
    "NIOS_7_12":  {"expected_min": 6,  "category": "board_exams",        "desc": "NIOS Class 7-12"},
    "IB_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "IB PYP Class 1-6"},
    "IB_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "IB MYP/DP Class 7-12"},
    "TN_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "TN Board Class 1-6"},
    "TN_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "TN Board Class 7-12"},
    "MH_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "MH Board Class 1-6"},
    "MH_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "MH Board Class 7-12"},
    "UP_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "UP Board Class 1-6"},
    "UP_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "UP Board Class 7-12"},
    "KA_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "KA Board Class 1-6"},
    "KA_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "KA Board Class 7-12"},

    # ── MISSING STATE BOARDS (need to add to queue) ──────────────
    "AP_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "AP Board Class 1-6"},
    "AP_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "AP Board Class 7-12"},
    "TS_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Telangana Board Class 1-6"},
    "TS_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Telangana Board Class 7-12"},
    "KL_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Kerala Board Class 1-6"},
    "KL_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Kerala Board Class 7-12"},
    "WB_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "WB Board Class 1-6"},
    "WB_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "WB Board Class 7-12"},
    "RJ_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Rajasthan Board Class 1-6"},
    "RJ_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Rajasthan Board Class 7-12"},
    "GJ_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Gujarat Board Class 1-6"},
    "GJ_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Gujarat Board Class 7-12"},
    "MP_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "MP Board Class 1-6"},
    "MP_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "MP Board Class 7-12"},
    "BR_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Bihar Board Class 1-6"},
    "BR_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Bihar Board Class 7-12"},
    "OR_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Odisha Board Class 1-6"},
    "OR_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Odisha Board Class 7-12"},
    "AS_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Assam Board Class 1-6"},
    "AS_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Assam Board Class 7-12"},
    "PB_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Punjab Board Class 1-6"},
    "PB_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Punjab Board Class 7-12"},
    "HR_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Haryana Board Class 1-6"},
    "HR_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Haryana Board Class 7-12"},
    "JH_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Jharkhand Board Class 1-6"},
    "JH_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Jharkhand Board Class 7-12"},
    "CG_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "CG Board Class 1-6"},
    "CG_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "CG Board Class 7-12"},
    "HP_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "HP Board Class 1-6"},
    "HP_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "HP Board Class 7-12"},
    "UK_1_6":     {"expected_min": 6,  "category": "board_exams",        "desc": "Uttarakhand Board Class 1-6"},
    "UK_7_12":    {"expected_min": 6,  "category": "board_exams",        "desc": "Uttarakhand Board Class 7-12"},
    "IGCSE_1_6":  {"expected_min": 6,  "category": "board_exams",        "desc": "Cambridge Primary Class 1-6"},
    "IGCSE_7_12": {"expected_min": 6,  "category": "board_exams",        "desc": "Cambridge IGCSE Class 7-12"},

    # ── SCHOLARSHIPS ──────────────────────────────────────────────
    "NTSE":           {"expected_min": 2,  "category": "scholarship",    "desc": "NTSE Stage 1 & 2"},
    "NMMS":           {"expected_min": 1,  "category": "scholarship",    "desc": "NMMS"},
    "KVPY":           {"expected_min": 3,  "category": "scholarship",    "desc": "KVPY SA/SX/SB"},
    "SOF_Olympiads":  {"expected_min": 3,  "category": "scholarship",    "desc": "NSO/IMO/IEO"},
    "INSPIRE":        {"expected_min": 1,  "category": "scholarship",    "desc": "INSPIRE SHE"},
    "NMMS_State":     {"expected_min": 5,  "category": "scholarship",    "desc": "State NMMS variants"},

    # ── SCHOOL ENTRANCES ─────────────────────────────────────────
    "Navodaya":       {"expected_min": 2,  "category": "school_entrance","desc": "JNVST Class 6 & 9"},
    "Sainik_School":  {"expected_min": 2,  "category": "school_entrance","desc": "AISSEE Class 6 & 9"},
    "KV_admission":   {"expected_min": 1,  "category": "school_entrance","desc": "KV Admission"},
    "RMS":            {"expected_min": 1,  "category": "school_entrance","desc": "Rashtriya Military Schools"},

    # ── UG ENGINEERING ────────────────────────────────────────────
    "JEE_Main":       {"expected_min": 2,  "category": "ug_entrance_engineering", "desc": "JEE Main Paper 1 & 2"},
    "JEE_Advanced":   {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "JEE Advanced Paper 1 & 2"},
    "BITSAT":         {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "BITSAT"},
    "VITEEE":         {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "VITEEE"},
    "SRMJEEE":        {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "SRMJEEE"},
    "KCET":           {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "Karnataka CET"},
    "MHT_CET":        {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "MHT CET"},
    "WBJEE":          {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "WB JEE"},
    "AP_EAPCET":      {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "AP EAPCET"},
    "TS_EAPCET":      {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "TS EAPCET"},
    "KEAM":           {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "Kerala KEAM"},
    "GUJCET":         {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "GUJCET"},
    "TNEA":           {"expected_min": 1,  "category": "ug_entrance_engineering", "desc": "TNEA Counselling"},

    # ── UG MEDICAL ────────────────────────────────────────────────
    "NEET_UG":        {"expected_min": 1,  "category": "ug_entrance_medical",     "desc": "NEET UG"},
    "AYUSH":          {"expected_min": 1,  "category": "ug_entrance_medical",     "desc": "AYUSH NEET"},
    "Nursing":        {"expected_min": 1,  "category": "ug_entrance_medical",     "desc": "AIIMS Nursing"},
    "JIPMER":         {"expected_min": 1,  "category": "ug_entrance_medical",     "desc": "JIPMER"},

    # ── UG OTHER ──────────────────────────────────────────────────
    "CLAT":           {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "CLAT UG"},
    "CUET_UG":        {"expected_min": 5,  "category": "ug_entrance_other",       "desc": "CUET UG subjects"},
    "NATA":           {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "Architecture NATA"},
    "NID_DAT":        {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "NID Design"},
    "ICAR_AIEEA":     {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "Agriculture ICAR"},
    "NCHM_JEE":       {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "Hotel Management"},
    "IMU_CET":        {"expected_min": 1,  "category": "ug_entrance_other",       "desc": "Maritime IMU"},

    # ── PG ENTRANCE ───────────────────────────────────────────────
    "GATE":           {"expected_min": 5,  "category": "pg_entrance",             "desc": "GATE all papers"},
    "CAT":            {"expected_min": 1,  "category": "pg_entrance",             "desc": "CAT MBA"},
    "MBA_Variants":   {"expected_min": 5,  "category": "pg_entrance",             "desc": "XAT CMAT MAT SNAP NMAT"},
    "CUET_PG":        {"expected_min": 1,  "category": "pg_entrance",             "desc": "CUET PG"},
    "NEET_PG":        {"expected_min": 1,  "category": "pg_entrance",             "desc": "NEET PG"},
    "NEET_MDS":       {"expected_min": 1,  "category": "pg_entrance",             "desc": "NEET MDS Dental"},
    "TANCET":         {"expected_min": 2,  "category": "pg_entrance",             "desc": "TANCET ME/MBA"},

    # ── PhD ───────────────────────────────────────────────────────
    "UGC_NET":        {"expected_min": 1,  "category": "phd_entrance",            "desc": "UGC NET"},
    "CSIR_NET":       {"expected_min": 1,  "category": "phd_entrance",            "desc": "CSIR NET"},
    "DBT_JRF":        {"expected_min": 1,  "category": "phd_entrance",            "desc": "DBT JRF"},
    "ICMR_JRF":       {"expected_min": 1,  "category": "phd_entrance",            "desc": "ICMR JRF"},
    "ICAR_JRF":       {"expected_min": 1,  "category": "phd_entrance",            "desc": "ICAR JRF"},

    # ── CENTRAL GOVT JOBS ─────────────────────────────────────────
    # UPSC
    "UPSC_CSE":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "UPSC IAS Prelims+Mains"},
    "UPSC_CDS":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "UPSC CDS"},
    "UPSC_NDA":       {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "UPSC NDA"},
    "UPSC_CAPF":      {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "UPSC CAPF AC"},
    "UPSC_ESE":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "UPSC Engineering Services"},
    "UPSC_CMSE":      {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "UPSC CMS"},
    "UPSC_IFS":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "UPSC Indian Forest Service"},
    "UPSC_GEOL":      {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "UPSC Geo-Scientist"},
    "UPSC_SO_Steno":  {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "UPSC SO/Steno"},
    # SSC
    "SSC_CGL":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC CGL Tier 1-4"},
    "SSC_CHSL":       {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC CHSL Tier 1-2"},
    "SSC_MTS":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC MTS Paper 1-2"},
    "SSC_GD":         {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC GD Constable"},
    "SSC_CPO":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC CPO SI/ASI"},
    "SSC_JE":         {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC Junior Engineer"},
    "SSC_Steno":      {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC Stenographer"},
    "SSC_JHT":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC Junior Hindi Translator"},
    "SSC_Selection":  {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SSC Selection Post"},
    # Railways
    "RRB_NTPC":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "RRB NTPC CBT1+CBT2"},
    "RRB_GroupD":     {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "RRB Group D"},
    "RRB_JE":         {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "RRB JE CBT1+CBT2"},
    "RRB_ALP":        {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "RRB ALP CBT1+CBT2"},
    "RRB_RPF":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "RPF Constable/SI"},
    # Banking
    "IBPS_PO":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "IBPS PO Prelims+Mains"},
    "IBPS_Clerk":     {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "IBPS Clerk"},
    "IBPS_SO":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "IBPS SO"},
    "IBPS_RRB":       {"expected_min": 2,  "category": "central_govt_jobs",       "desc": "IBPS RRB PO+Clerk"},
    "SBI_PO":         {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SBI PO"},
    "SBI_Clerk":      {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "SBI Clerk"},
    "RBI_Grade_B":    {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "RBI Grade B"},
    "RBI_Asst":       {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "RBI Assistant"},
    "NABARD":         {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "NABARD Grade A/B"},
    # Insurance
    "LIC_AAO":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "LIC AAO"},
    "LIC_ADO":        {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "LIC ADO"},
    # PSUs
    "DRDO_CEPTAM":    {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "DRDO CEPTAM"},
    "ISRO_Scientist": {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "ISRO Scientist"},
    "BARC":           {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "BARC OCES/DGFS"},
    "ONGC":           {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "ONGC recruitment"},
    "India_Post_GDS": {"expected_min": 1,  "category": "central_govt_jobs",       "desc": "India Post GDS"},

    # ── STATE PSC ────────────────────────────────────────────────
    "TNPSC":          {"expected_min": 3,  "category": "state_psc",               "desc": "TNPSC Group 1,2,4"},
    "UPPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "UPPSC PCS Prelims+Mains"},
    "KPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "KPSC KAS"},
    "MPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "MPSC State Service"},
    "APPSC":          {"expected_min": 3,  "category": "state_psc",               "desc": "APPSC Group 1,2,3"},
    "TSPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "TSPSC Group 1,2"},
    "Kerala_PSC":     {"expected_min": 3,  "category": "state_psc",               "desc": "Kerala PSC"},
    "WBPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "WBPSC WBCS"},
    "RPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "RPSC RAS"},
    "GPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "GPSC"},
    "MPPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "MPPSC State Service"},
    "BPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "BPSC 67th+"},
    "JPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "JPSC"},
    "OPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "OPSC OAS"},
    "APSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "APSC ACS"},
    "PPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "PPSC"},
    "HPSC":           {"expected_min": 2,  "category": "state_psc",               "desc": "HPSC HCS"},
    "HPPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "HPPSC"},
    "UKPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "UKPSC"},
    "CGPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "CGPSC State Service"},
    "JKPSC":          {"expected_min": 2,  "category": "state_psc",               "desc": "JKPSC KAS"},

    # ── MILITARY ─────────────────────────────────────────────────
    "NDA":            {"expected_min": 1,  "category": "military",                "desc": "NDA Written+SSB"},
    "CDS":            {"expected_min": 2,  "category": "military",                "desc": "CDS OTA+IMA"},
    "AFCAT":          {"expected_min": 1,  "category": "military",                "desc": "AFCAT"},
    "Agniveer":       {"expected_min": 3,  "category": "military",                "desc": "Agniveer Army/Navy/Air"},
    "CAPF_GD":        {"expected_min": 1,  "category": "military",                "desc": "CAPF GD Constable"},
    "SSB_Process":    {"expected_min": 1,  "category": "military",                "desc": "SSB Selection Process"},
    "Coast_Guard":    {"expected_min": 2,  "category": "military",                "desc": "ICG Navik/Yantrik"},

    # ── PROFESSIONAL ──────────────────────────────────────────────
    "CA":             {"expected_min": 3,  "category": "professional",            "desc": "CA Foundation+Inter+Final"},
    "CS":             {"expected_min": 2,  "category": "professional",            "desc": "CS Executive+Professional"},
    "CMA":            {"expected_min": 3,  "category": "professional",            "desc": "CMA Foundation+Inter+Final"},
    "Actuarial":      {"expected_min": 1,  "category": "professional",            "desc": "IAI Actuarial exams"},
    "NISM":           {"expected_min": 5,  "category": "professional",            "desc": "NISM Series 1A-21A"},
    "IRDAI":          {"expected_min": 2,  "category": "professional",            "desc": "IRDAI Agent+Surveyor"},
    "CFA":            {"expected_min": 3,  "category": "professional",            "desc": "CFA Level 1,2,3"},
    "FRM":            {"expected_min": 2,  "category": "professional",            "desc": "FRM Part 1,2"},

    # ── TECH CERTIFICATIONS ───────────────────────────────────────
    "AWS":            {"expected_min": 2,  "category": "tech_certifications",     "desc": "AWS Cloud Practitioner+SAA"},
    "Azure":          {"expected_min": 2,  "category": "tech_certifications",     "desc": "Azure AZ-900+AZ-104"},
    "GCP":            {"expected_min": 2,  "category": "tech_certifications",     "desc": "GCP ACE+Professional"},
    "Cisco_CCNA":     {"expected_min": 3,  "category": "tech_certifications",     "desc": "CCNA/CCNP/CCIE"},
    "CompTIA":        {"expected_min": 4,  "category": "tech_certifications",     "desc": "A+/Net+/Sec+/CySA+"},
    "Kubernetes":     {"expected_min": 3,  "category": "tech_certifications",     "desc": "CKA/CKAD/CKS"},
    "CEH_OSCP":       {"expected_min": 2,  "category": "tech_certifications",     "desc": "CEH+OSCP"},

    # ── COMPANY EXAMS ────────────────────────────────────────────
    "TCS":            {"expected_min": 1,  "category": "company_exams",           "desc": "TCS NQT"},
    "Infosys":        {"expected_min": 1,  "category": "company_exams",           "desc": "Infosys InfyTQ"},
    "Wipro":          {"expected_min": 1,  "category": "company_exams",           "desc": "Wipro WILP"},
    "Cognizant":      {"expected_min": 1,  "category": "company_exams",           "desc": "CTS GenC Pro"},
    "Accenture":      {"expected_min": 1,  "category": "company_exams",           "desc": "Accenture recruitment"},
    "Zoho":           {"expected_min": 1,  "category": "company_exams",           "desc": "Zoho coding test"},

    # ── LANGUAGE / FOREIGN ────────────────────────────────────────
    "IELTS":          {"expected_min": 2,  "category": "language_foreign",        "desc": "IELTS Academic+General"},
    "TOEFL":          {"expected_min": 1,  "category": "language_foreign",        "desc": "TOEFL iBT"},
    "GRE":            {"expected_min": 1,  "category": "language_foreign",        "desc": "GRE General"},
    "GMAT":           {"expected_min": 1,  "category": "language_foreign",        "desc": "GMAT Focus"},
    "SAT":            {"expected_min": 1,  "category": "language_foreign",        "desc": "SAT"},
    "PTE":            {"expected_min": 1,  "category": "language_foreign",        "desc": "PTE Academic"},
    "JLPT":           {"expected_min": 5,  "category": "language_foreign",        "desc": "JLPT N1-N5"},
    "DELF_DALF":      {"expected_min": 4,  "category": "language_foreign",        "desc": "DELF A1-B2 DALF C1-C2"},
    "HSK":            {"expected_min": 6,  "category": "language_foreign",        "desc": "HSK 1-6"},
    "USMLE":          {"expected_min": 3,  "category": "language_foreign",        "desc": "USMLE Step 1,2,3"},
    "PLAB":           {"expected_min": 2,  "category": "language_foreign",        "desc": "PLAB 1,2"},
    "NCLEX":          {"expected_min": 1,  "category": "language_foreign",        "desc": "NCLEX-RN"},

    # ── SKILL / VOCATIONAL ────────────────────────────────────────
    "ITI":            {"expected_min": 3,  "category": "skill_vocational",        "desc": "ITI Fitter/Electrician/Welder+"},
    "PMKVY":          {"expected_min": 3,  "category": "skill_vocational",        "desc": "PMKVY sector assessments"},
    "Apprenticeship": {"expected_min": 1,  "category": "skill_vocational",        "desc": "NAPS Apprenticeship"},

    # ── NEP / PARAKH ──────────────────────────────────────────────
    "PARAKH":         {"expected_min": 1,  "category": "nep_parakh",              "desc": "PARAKH NAS"},
    "NIPUN":          {"expected_min": 1,  "category": "nep_parakh",              "desc": "NIPUN FLN"},
    "SAFAL":          {"expected_min": 1,  "category": "nep_parakh",              "desc": "SAFAL Class 3,5,8"},
}


def get_supabase():
    from supabase import create_client
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    return create_client(url, key)


def full_audit():
    sb = get_supabase()
    rows = sb.table("exams").select("id, name, subcategory, category, tiers, confidence").execute().data

    counts = Counter(r["subcategory"] for r in rows)
    tier_counts = defaultdict(list)
    for r in rows:
        tiers = r.get("tiers") or []
        tier_counts[r["subcategory"]].append(len(tiers))

    print("\n" + "═"*70)
    print("  📊 TRYIT EXAM DATABASE — FULL AUDIT REPORT")
    print("═"*70)
    print(f"\n  Total rows in Supabase : {len(rows)}")
    print(f"  Unique subcategories   : {len(counts)}")
    print(f"  Master list size       : {len(MASTER_EXAM_LIST)}")

    # ── PRESENT ──
    print("\n✅ PRESENT (in Supabase):")
    print(f"  {'Subcategory':<25} {'Rows':>5}  {'Avg Tiers':>9}  {'Status'}")
    print(f"  {'-'*25}  {'-'*5}  {'-'*9}  {'-'*20}")

    present = []
    thin = []
    for sub, info in MASTER_EXAM_LIST.items():
        if sub in counts:
            avg_tiers = sum(tier_counts[sub]) / len(tier_counts[sub]) if tier_counts[sub] else 0
            expected = info["expected_min"]
            row_count = counts[sub]
            status = "✅ OK"
            if row_count < expected:
                status = f"⚠️  only {row_count}/{expected} expected"
                thin.append(sub)
            if avg_tiers < 1:
                status += " | ❌ no tiers"
                thin.append(sub)
            print(f"  {sub:<25} {row_count:>5}  {avg_tiers:>8.1f}  {status}")
            present.append(sub)

    # ── MISSING ──
    missing = [s for s in MASTER_EXAM_LIST if s not in counts]
    print(f"\n❌ MISSING ({len(missing)} subcategories):")
    for sub in missing:
        info = MASTER_EXAM_LIST[sub]
        print(f"  ❌ {sub:<25} — needs {info['expected_min']}+ rows — {info['desc']}")

    # ── DUPLICATES ──
    print(f"\n🔁 CHECKING DUPLICATES (same name in same subcategory):")
    name_counts = Counter((r["name"], r["subcategory"]) for r in rows)
    dups = [(name, sub, cnt) for (name, sub), cnt in name_counts.items() if cnt > 1]
    if dups:
        for name, sub, cnt in dups:
            print(f"  ⚠️  '{name}' in {sub} appears {cnt} times")
    else:
        print("  ✅ No duplicates found")

    # ── EXTRA (not in master list) ──
    extra = [s for s in counts if s not in MASTER_EXAM_LIST]
    if extra:
        print(f"\n📦 EXTRA (in DB but not in master list — {len(extra)}):")
        for sub in extra:
            print(f"  📦 {sub}: {counts[sub]} rows")

    # ── SUMMARY ──
    print("\n" + "═"*70)
    print(f"  ✅ Present  : {len(present)}/{len(MASTER_EXAM_LIST)}")
    print(f"  ❌ Missing  : {len(missing)}/{len(MASTER_EXAM_LIST)}")
    print(f"  ⚠️  Thin     : {len(set(thin))}")
    print(f"  🔁 Dup groups: {len(dups)}")
    print(f"  📦 Extra    : {len(extra)}")
    print("═"*70)

    return missing, thin, dups


def fix_duplicates():
    """Remove duplicate rows — keep the one with most tiers."""
    sb = get_supabase()
    rows = sb.table("exams").select("id, name, subcategory, tiers").execute().data

    from collections import defaultdict
    groups = defaultdict(list)
    for r in rows:
        groups[(r["name"], r["subcategory"])].append(r)

    removed = 0
    for (name, sub), group in groups.items():
        if len(group) > 1:
            # Keep the one with most tiers
            group.sort(key=lambda x: len(x.get("tiers") or []), reverse=True)
            keep = group[0]
            for r in group[1:]:
                sb.table("exams").delete().eq("id", r["id"]).execute()
                print(f"  🗑️  Removed dup: '{name}' ({sub}) id={r['id']}")
                removed += 1

    print(f"\n✅ Removed {removed} duplicate rows")


def fix_missing(missing_subs):
    """Auto-generate missing subcategories."""
    if not missing_subs:
        print("✅ Nothing missing to fix!")
        return

    print(f"\n🔧 Auto-generating {len(missing_subs)} missing subcategories...")

    # Add missing to category_queue dynamically and run
    import subprocess
    for sub in missing_subs:
        info = MASTER_EXAM_LIST.get(sub, {})
        print(f"\n▶ Generating: {sub} ({info.get('desc', '')})")
        result = subprocess.run(
            ["python", "exam_generator.py", "--subcategory", sub],
            capture_output=False
        )


def main():
    parser = argparse.ArgumentParser(description="TryIT Exam DB Audit & Fix")
    parser.add_argument("--fix",        action="store_true", help="Auto-fix missing subcategories")
    parser.add_argument("--duplicates", action="store_true", help="Remove duplicate rows")
    parser.add_argument("--thin",       action="store_true", help="Show thin entries only")
    args = parser.parse_args()

    missing, thin, dups = full_audit()

    if args.duplicates:
        fix_duplicates()

    if args.fix:
        fix_missing(missing)

    if not any([args.fix, args.duplicates, args.thin]):
        print("\n💡 To fix issues, run:")
        print("   python audit_and_fix.py --duplicates   # remove dups")
        print("   python audit_and_fix.py --fix          # generate missing")
        print("   python audit_and_fix.py --fix --duplicates  # both\n")


if __name__ == "__main__":
    main()
