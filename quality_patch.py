"""
Quality patch for generate_master.py v8
Applies all 4 approved changes:
1. Quality threshold per level (6/7/7/8)
2. Auto-retry on soft rejection
3. NVIDIA upgrade for L7-10
4. Batch=5 for L7-10, batch=7 for L1-6
"""

content = open('generate_master.py', encoding='utf-8').read()
patches = 0

# ── PATCH 1: Replace fixed BATCH_SIZE with dynamic per-level batch ────────────
old1 = '''# ── CONSTANTS ──────────────────────────────────────────────────────────────────
BATCH_SIZE         = 7     # Questions per API call (up from 5)
CONCURRENT_WORKERS = 3     # Parallel topic threads
QUALITY_THRESHOLD  = 6     # Min score to save
GROQ_INTERVAL      = 3.5   # Seconds between Groq calls (org-wide rate limit)

# Level targets: more questions at easy levels
def get_target(level):
    if level <= 3: return 30
    if level <= 6: return 20
    if level == 7: return 15
    if level <= 9: return 10
    return 5'''

new1 = '''# ── CONSTANTS ──────────────────────────────────────────────────────────────────
CONCURRENT_WORKERS = 3     # Parallel topic threads
GROQ_INTERVAL      = 3.5   # Seconds between Groq calls (org-wide rate limit)

def get_batch_size(level):
    """Batch=7 for easy levels, batch=5 for hard (less truncation risk)"""
    return 7 if level <= 6 else 5

def get_quality_threshold(level):
    """Stricter quality at higher levels"""
    if level <= 3: return 6   # Lenient - volume matters for school
    if level <= 6: return 7   # Moderate - exam alignment critical
    if level <= 8: return 7   # Strict - misconceptions must be named
    return 8                   # Very strict - expert depth required

def get_target(level):
    if level <= 3: return 30
    if level <= 6: return 20
    if level == 7: return 15
    if level <= 9: return 10
    return 5'''

if old1 in content:
    content = content.replace(old1, new1)
    patches += 1
    print("PATCH 1 OK: Dynamic batch size and quality threshold per level")
else:
    print("PATCH 1 FAIL: Constants block not found")

# ── PATCH 2: Replace nvidia_upgrade to cover L7-10 instead of L8-10 ──────────
old2 = '            if level >= 8:\n                q = nvidia_upgrade(q, topic_name, level, exam_tags)'
new2 = '            if level >= 7:\n                q = nvidia_upgrade(q, topic_name, level, exam_tags)'

if old2 in content:
    content = content.replace(old2, new2)
    patches += 1
    print("PATCH 2 OK: NVIDIA upgrade now covers L7-10")
else:
    print("PATCH 2 FAIL: nvidia_upgrade call not found - checking...")
    for i, line in enumerate(content.split('\n')):
        if 'nvidia_upgrade' in line and 'level' in line:
            print(f"  Found at line {i}: {repr(line)}")

# ── PATCH 3: Replace fixed batch in process_topic_level with dynamic ──────────
old3 = '''    while saved < needed and empty < 3:
        batch = min(BATCH_SIZE, needed - saved)
        questions = generate_batch(topic_id, topic_name, subject_id, level,
                                   batch, exam_tags, exam_patterns)
        if not questions:
            empty += 1
            print(f"   Empty {empty}/3 - wait 5s", flush=True)
            time.sleep(5)
            continue

        empty = 0
        for q in questions:
            # NVIDIA upgrade for L8-10
            if level >= 7:
                q = nvidia_upgrade(q, topic_name, level, exam_tags)

            # Gemini QA gate
            passed, score, reason = gemini_qa(q, level)
            if not passed or score < QUALITY_THRESHOLD:
                continue

            if save_question(q, topic_id, subject_id, level, exam_tags, score):
                saved += 1
                print(f"      saved {saved}/{needed} L{level} score={score}", flush=True)

        time.sleep(0.5)'''

new3 = '''    qa_threshold = get_quality_threshold(level)
    batch_size   = get_batch_size(level)

    while saved < needed and empty < 3:
        batch = min(batch_size, needed - saved)
        questions = generate_batch(topic_id, topic_name, subject_id, level,
                                   batch, exam_tags, exam_patterns)
        if not questions:
            empty += 1
            print(f"   Empty {empty}/3 - wait 5s", flush=True)
            time.sleep(5)
            continue

        empty = 0
        for q in questions:
            # NVIDIA upgrade for L7-10 (approved: extend from L8 to L7)
            if level >= 7:
                q = nvidia_upgrade(q, topic_name, level, exam_tags)

            # Gemini QA gate with level-specific threshold
            passed, score, reason = gemini_qa(q, level)

            # Auto-retry on soft rejection (story/shortcut issue only)
            if not passed and score >= 4 and reason and any(
                soft in reason.lower() for soft in
                ["story","shortcut","trick","connect","tip","incomplete"]):
                # Regenerate story only - reuse question skeleton
                q = retry_story(q, topic_name, level, exam_tags)
                passed, score, reason = gemini_qa(q, level)
                if passed:
                    print(f"      Retry story OK score={score}", flush=True)

            if not passed or score < qa_threshold:
                print(f"      Rejected L{level} score={score} threshold={qa_threshold}: {reason[:40]}", flush=True)
                continue

            if save_question(q, topic_id, subject_id, level, exam_tags, score):
                saved += 1
                print(f"      saved {saved}/{needed} L{level} score={score}", flush=True)

        time.sleep(0.5)'''

if old3 in content:
    content = content.replace(old3, new3)
    patches += 1
    print("PATCH 3 OK: Dynamic batch, level threshold, auto-retry on soft rejection")
else:
    print("PATCH 3 FAIL: process_topic_level while loop not found")

# ── PATCH 4: Add retry_story function before process_topic_level ──────────────
old4 = '# ── PROCESS TOPIC LEVEL ───────────────────────────────────────────────────────'
new4 = '''# ── RETRY STORY (soft rejection handler) ──────────────────────────────────────
def retry_story(q, topic_name, level, exam_tags):
    """Regenerate only story_explanation and shortcut_tips when QA soft-rejects."""
    exam_str = ", ".join(exam_tags[:3]) if exam_tags else "SSC CGL, UPSC"
    correct  = q["options"][q["correct_answer"]]

    prompt = f"""Fix the story and shortcut for this MCQ. Keep the question and options UNCHANGED.

Question: {q.get("question","")}
Correct Answer: {correct} (index {q.get("correct_answer",0)})
Topic: {topic_name} | Level: {level}/10 | Exam: {exam_str}

{story_guide(level)}

RULES:
- story_explanation MUST end with: "This is exactly why {correct} is the answer."
- Character must face the SAME problem as question
- Solve with SAME logic as correct answer
- shortcut_tips MUST have: TRICK NAME + HOW + APPLY HERE + EXAM TIP

Return ONLY JSON object:
{{"story_explanation": "4-sentence Indian story ending with This is exactly why...",
  "shortcut_tips": "TRICK NAME:... HOW:... APPLY HERE:... EXAM TIP:..."}}"""

    msgs = [{"role":"user","content":prompt}]

    # Try Groq first (fast)
    groq_rate_wait()
    raw = call_openai(GROQ_POOL, GROQ_CLIENTS, "openai/gpt-oss-120b", msgs,
                      max_tokens=800, timeout=30, label="RetryGroq")
    if raw:
        data = extract_obj(raw)
        if data and data.get("story_explanation") and "This is exactly why" in data.get("story_explanation",""):
            q["story_explanation"] = data["story_explanation"]
            if data.get("shortcut_tips"):
                q["shortcut_tips"] = data["shortcut_tips"]
            return q

    # Try Gemini generation pool
    if GEMINI_GEN_POOL:
        raw = call_gemini_rest(GEMINI_GEN_POOL, GEMINI_KEY_TO_MODEL, prompt, "RetryGemini")
        if raw:
            data = extract_obj(raw)
            if data and data.get("story_explanation") and "This is exactly why" in data.get("story_explanation",""):
                q["story_explanation"] = data["story_explanation"]
                if data.get("shortcut_tips"):
                    q["shortcut_tips"] = data["shortcut_tips"]
                return q

    return q  # Return original if retry fails

# ── PROCESS TOPIC LEVEL ───────────────────────────────────────────────────────'''

if old4 in content:
    content = content.replace(old4, new4)
    patches += 1
    print("PATCH 4 OK: retry_story function added")
else:
    print("PATCH 4 FAIL: process_topic_level header not found")

# ── PATCH 5: Update Gemini QA prompt with level-specific checks ───────────────
old5 = '''CHECK ALL STRICTLY:
1. Difficulty EXACTLY matches Level {level}/10: {diff_guide(level)[:60]}
2. Correct answer is factually accurate?
3. why_correct has step-by-step proof (not just restatement)?
4. story_explanation: Indian character faces SAME problem, solves with SAME logic, ends "This is exactly why [option] is the answer"?
5. shortcut_tips has TRICK NAME + HOW + APPLY HERE?
6. Wrong option explanations name SPECIFIC misconceptions?

Return ONLY JSON: {{"passed":true,"score":8,"reason":"one sentence"}}
Score 1-10. Pass if score>=6 AND checks 1,2,3 all pass.
Reject: wrong difficulty, factual error, story doesn't connect to answer.'''

new5 = '''CHECK ALL STRICTLY:
1. Difficulty EXACTLY matches Level {level}/10: {diff_guide(level)[:60]}
2. Correct answer is factually accurate?
3. why_correct has step-by-step proof (not just restatement)?
4. story_explanation: Indian character faces SAME problem, solves with SAME logic, ends EXACTLY "This is exactly why [option letter and text] is the answer"?
5. shortcut_tips has TRICK NAME + HOW + APPLY HERE + EXAM TIP (all 4 parts)?
6. Wrong option explanations name SPECIFIC misconceptions (not just "this is wrong")?
7. {"Language is appropriate for Class 1-6 students (simple, no jargon)?" if level<=6 else "All 4 options are plausible to an average student at this level?"}

Return ONLY JSON: {{"passed":true,"score":8,"reason":"one sentence - what passed or what specific thing failed"}}
Score 1-10.
Minimum passing score for this level: {"6" if level<=3 else "7" if level<=8 else "8"}/10
Reject immediately if: wrong difficulty, factual error, story doesn't end with required sentence, or {"language too complex for school level" if level<=6 else "options not plausible enough for expert level"}.'''

if old5 in content:
    content = content.replace(old5, new5)
    patches += 1
    print("PATCH 5 OK: Gemini QA prompt updated with level-specific checks")
else:
    print("PATCH 5 FAIL: Gemini QA prompt not found")

# Save
open('generate_master.py', 'w', encoding='utf-8').write(content)
print(f"\nTotal patches applied: {patches}/5")
print(f"File size: {len(content)} chars")

# Verify key changes
verifications = {
    'get_batch_size':      'get_batch_size' in content,
    'get_quality_threshold': 'get_quality_threshold' in content,
    'retry_story':         'retry_story' in content,
    'nvidia L7+':          'level >= 7' in content,
    'level-specific QA':   'Minimum passing score for this level' in content,
    'auto-retry soft':     'retry_story(q, topic_name' in content,
}
print("\nVerification:")
for k,v in verifications.items():
    print(f"  {k}: {'PASS' if v else 'FAIL'}")
