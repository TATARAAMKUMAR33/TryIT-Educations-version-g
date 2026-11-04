def generate_batch(topic_id, topic_name, subject_id, level, count, exam_tags):
    context = get_context(topic_id) if callable(get_context) else ""
    exam_str = ", ".join(exam_tags[:6]) if exam_tags else "UPSC, SSC CGL, RRB NTPC"

    prompt = f"""You are an expert MCQ writer for Indian competitive exams.
Generate exactly {count} high-quality MCQs for:
Topic: {topic_name}
Subject: {subject_id}
Difficulty Level: {level}/10
Relevant Exams: {exam_str}
Context: {context}

RULES:
1. Each question must be UNIQUE.
2. Difficulty {level}/10: {'Recall/basic understanding' if level <= 3 else 'Application of concepts' if level <= 6 else 'Analysis, multi-step reasoning, trap options'}.
3. The why_correct field MUST contain step-by-step logic.
4. All 4 options must be plausible.
5. For levels 8-10: include trap options that test common misconceptions.

Output ONLY a valid JSON array, no preamble, no markdown:
[
  {{
    "question": "...",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": 0,
    "why_correct": "Step-by-step: ...",
    "why_wrong_option_b": "Misconception: ...",
    "why_wrong_option_c": "Misconception: ...",
    "why_wrong_option_d": "Misconception: ...",
    "story_explanation": "Ramu/Priya anecdote...",
    "shortcut_tips": "Mnemonic or 10-second trick...",
    "cross_exam_intelligence": "This exact type appears in UPSC Prelims as..., SSC CGL as..."
  }}
]"""

    for tier_name, pool, clients in GENERATION_TIERS:
        if not clients:
            continue

        tried_indices = set()

        while len(tried_indices) < len(clients):
            idx, key = pool.get_key(wait=False)

            if key is None:
                print(f"      ↷ {tier_name} exhausted → next tier", flush=True)
                break

            if idx in tried_indices:
                print(f"      ↷ {tier_name} exhausted → next tier", flush=True)
                break

            tried_indices.add(idx)

            if idx >= len(clients):
                pool.mark_error(idx)
                continue

            _, client, model = clients[idx]

            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a JSON-only MCQ generator. Output ONLY valid JSON arrays with no preamble."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4096,
                    timeout=90,
                )
                raw = resp.choices[0].message.content or ""

                if not raw.strip():
                    print(f"      ⚠️  {tier_name} key#{idx+1} empty response", flush=True)
                    pool.mark_error(idx)
                    continue

                data = extract_json_array(raw)

                if not data:
                    print(f"      ⚠️  {tier_name} key#{idx+1} JSON parse failed. Raw snippet: {raw[:300]}", flush=True)
                    pool.mark_error(idx)
                    continue

                valid = _validate_questions(data)
                if valid:
                    pool.mark_success(idx)
                    print(f"      ✅ {len(valid)}/{len(data)} via {tier_name} [{model}]", flush=True)
                    return valid
                else:
                    print(f"      ⚠️  {tier_name} key#{idx+1} questions failed validation", flush=True)
                    pool.mark_error(idx)

            except Exception as e:
                err = str(e)
                if "429" in err or "rate" in err.lower() or "quota" in err.lower():
                    pool.mark_rate_limit(idx, cooldown=65)
                    print(f"      ⏳ {tier_name} key#{idx+1} rate-limited", flush=True)
                elif "401" in err or "403" in err:
                    pool.mark_dead(idx, reason="invalid key")
                    print(f"      ❌ {tier_name} key#{idx+1} dead — invalid key", flush=True)
                elif "timeout" in err.lower() or "timed out" in err.lower():
                    pool.mark_rate_limit(idx, cooldown=30)
                    print(f"      ⏱️  {tier_name} key#{idx+1} timeout", flush=True)
                else:
                    print(f"      ⚠️  {tier_name} key#{idx+1} error: {err[:80]}", flush=True)
                    pool.mark_error(idx)
                continue

        print(f"      ↷ {tier_name} exhausted → next tier", flush=True)

    print("      ⚠️  All tiers failed for this batch", flush=True)
    return []
