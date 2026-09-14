"""
analyzer.py

All the "intelligence" in the app lives here, implemented as
transparent, rule-based scoring so it works with zero external API
calls. Every function returns plain dicts/lists that map directly
onto the frontend's JSON expectations.

If AI_PROVIDER is configured with a real key (see config.py), the
functions in this file are the fallback path — swap in an AI call
per-function later without touching the rest of the app.
"""

import re

from job_roles import JOB_ROLES, ROLE_NAMES, get_required_skills, guess_role_from_skills

REQUIRED_SECTIONS = ["education", "experience", "skills", "projects"]

STANDARD_HEADINGS = ["summary", "education", "experience", "skills", "projects"]


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def score_ats_compatibility(parsed):
    """Checks standard headings, contact info, length, keywords, formatting proxies."""
    score = 0
    reasons = []

    # Standard section headings (30 pts)
    present_headings = sum(1 for s in STANDARD_HEADINGS if parsed["sections"].get(s))
    heading_score = round((present_headings / len(STANDARD_HEADINGS)) * 30)
    score += heading_score
    reasons.append(f"{present_headings}/{len(STANDARD_HEADINGS)} standard section headings found (+{heading_score})")

    # Contact info completeness (15 pts)
    contact = parsed["contact"]
    contact_hits = sum(1 for k in ("email", "phone") if contact.get(k))
    contact_score = round((contact_hits / 2) * 15)
    score += contact_score
    reasons.append(f"Contact details found: {contact_hits}/2 (email, phone) (+{contact_score})")

    # Resume length (15 pts) - sweet spot 300-900 words
    wc = parsed["word_count"]
    if 300 <= wc <= 900:
        length_score = 15
    elif 150 <= wc < 300 or 900 < wc <= 1200:
        length_score = 10
    else:
        length_score = 4
    score += length_score
    reasons.append(f"Resume length is {wc} words (+{length_score})")

    # Action verbs (15 pts)
    verbs = parsed["action_verb_count"]
    verb_score = _clamp(round((verbs / 8) * 15), 0, 15)
    score += verb_score
    reasons.append(f"{verbs} strong action verbs detected (+{verb_score})")

    # Quantifiable achievements (15 pts)
    quant = parsed["quantifiable_achievements"]
    quant_score = _clamp(round((quant / 4) * 15), 0, 15)
    score += quant_score
    reasons.append(f"{quant} quantifiable achievements (numbers/%/$) detected (+{quant_score})")

    # Skills keyword density (10 pts)
    skill_score = _clamp(round((len(parsed["skills"]) / 8) * 10), 0, 10)
    score += skill_score
    reasons.append(f"{len(parsed['skills'])} recognised skill keywords found (+{skill_score})")

    return {
        "score": _clamp(round(score)),
        "reasons": reasons,
    }


def score_categories(parsed, ats_result):
    content_quality = _clamp(
        round(40 + parsed["action_verb_count"] * 4 + parsed["quantifiable_achievements"] * 6)
    )
    skills_score = _clamp(round((len(parsed["skills"]) / 10) * 100))
    formatting_score = _clamp(
        round(50 + sum(1 for s in REQUIRED_SECTIONS if parsed["sections"].get(s)) * 12)
    )
    keyword_score = _clamp(round((len(parsed["skills"]) / 12) * 100))

    return {
        "ats_compatibility": ats_result["score"],
        "content_quality": content_quality,
        "skills": skills_score,
        "formatting": formatting_score,
        "keyword_optimization": keyword_score,
    }


def resume_strength_label(overall_score):
    if overall_score >= 85:
        return "Excellent"
    if overall_score >= 70:
        return "Good"
    if overall_score >= 50:
        return "Needs Work"
    return "Weak"


def build_checklist(parsed):
    contact = parsed["contact"]
    items = [
        {"label": "Contact information present", "passed": bool(contact.get("email") and contact.get("phone"))},
        {"label": "Education section present", "passed": bool(parsed["sections"].get("education"))},
        {"label": "Skills section present", "passed": bool(parsed["sections"].get("skills"))},
        {"label": "Projects section present", "passed": bool(parsed["sections"].get("projects"))},
        {"label": "Experience section present", "passed": bool(parsed["sections"].get("experience"))},
        {"label": "Quantifiable achievements included", "passed": parsed["quantifiable_achievements"] >= 2},
        {"label": "LinkedIn profile included", "passed": bool(contact.get("linkedin"))},
        {"label": "GitHub profile included", "passed": bool(contact.get("github"))},
    ]
    completeness = round(sum(1 for i in items if i["passed"]) / len(items) * 100)
    return {"items": items, "completeness": completeness}


def build_recommendations(parsed, checklist):
    recs = []

    def add(category, text, priority):
        recs.append({"category": category, "text": text, "priority": priority})

    if parsed["quantifiable_achievements"] < 2:
        add("Content", "Add measurable achievements (numbers, %, time saved) to your bullet points.", "High")
    if parsed["action_verb_count"] < 5:
        add("Content", "Start bullet points with strong action verbs like 'built', 'led', or 'optimized'.", "Medium")
    add("Content", "Trim unnecessary information that doesn't support your target role.", "Low")

    if len(parsed["skills"]) < 6:
        add("Skills", "Add more relevant technical skills that match your target job role.", "High")
    add("Skills", "Explicitly name the tools and libraries you used in each project.", "Medium")

    if not parsed["sections"].get("skills"):
        add("Formatting", "Add a clearly labeled 'Skills' section with standard heading text.", "High")
    add("Formatting", "Keep headings and spacing consistent throughout the document.", "Low")
    add("Formatting", "Avoid tables, columns, or graphics that can confuse ATS parsers.", "Medium")

    if checklist["completeness"] < 80:
        add("ATS Optimization", "Use standard section headings (Experience, Education, Skills, Projects).", "High")
    add("ATS Optimization", "Mirror important keywords from job descriptions you're targeting.", "Medium")
    add("ATS Optimization", "Avoid complicated multi-column layouts that ATS parsers can misread.", "Medium")

    return recs


def skill_gap_analysis(found_skills, role_name):
    required = get_required_skills(role_name)
    found_lower = {s.lower() for s in found_skills}

    breakdown = []
    for skill, weight in sorted(required.items(), key=lambda kv: -kv[1]):
        has_it = skill in found_lower
        # A skill you have scores near-full strength; a missing one shows as a gap.
        strength = 90 if has_it else _clamp(weight * 3, 5, 35)
        breakdown.append({
            "skill": skill,
            "have": has_it,
            "strength": strength,
            "importance": weight,
        })

    total_weight = sum(required.values()) or 1
    matched_weight = sum(w for s, w in required.items() if s in found_lower)
    overall_match = round((matched_weight / total_weight) * 100)

    missing = [b["skill"] for b in breakdown if not b["have"]]

    return {
        "role": role_name,
        "overall_match": overall_match,
        "breakdown": breakdown,
        "missing_skills": missing,
    }


def _tokenize_keywords(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z+./-]{2,}", text.lower())
    stop = {"the", "and", "for", "with", "you", "will", "are", "our", "your",
            "this", "that", "have", "who", "from", "not", "able", "can",
            "job", "role", "work", "team", "years", "experience"}
    return {w for w in words if w not in stop}


def job_description_match(resume_skills, resume_text, job_description):
    jd_keywords = _tokenize_keywords(job_description)
    resume_keywords = _tokenize_keywords(resume_text)
    resume_skill_set = {s.lower() for s in resume_skills}

    # Skills match: known skills mentioned in JD vs found in resume
    jd_known_skills = {s for s in JOB_ROLES_FLAT_SKILLS() if s in job_description.lower()}
    matched_skills = sorted(jd_known_skills & resume_skill_set)
    missing_skill_keywords = sorted(jd_known_skills - resume_skill_set)
    skills_match = round((len(matched_skills) / len(jd_known_skills)) * 100) if jd_known_skills else 70

    # Keyword match: general vocabulary overlap
    if jd_keywords:
        keyword_overlap = jd_keywords & resume_keywords
        keyword_match = round((len(keyword_overlap) / len(jd_keywords)) * 100)
    else:
        keyword_match = 0

    # Experience / education match: light heuristic based on presence of years/degree mentions
    experience_match = 80 if re.search(r"\d+\+?\s+years?", resume_text.lower()) or "intern" in resume_text.lower() else 60
    education_match = 90 if re.search(r"b\.?tech|bachelor|master|degree", resume_text.lower()) else 55

    overall = round(
        skills_match * 0.4 + keyword_match * 0.25 + experience_match * 0.2 + education_match * 0.15
    )

    recommended_changes = []
    if missing_skill_keywords:
        recommended_changes.append(
            f"Add these skills if you genuinely have them: {', '.join(missing_skill_keywords[:6])}."
        )
    if keyword_match < 60:
        recommended_changes.append("Mirror more of the job description's exact phrasing where it's honest to do so.")
    if experience_match < 70:
        recommended_changes.append("Make your years of experience or internship duration explicit.")
    if not recommended_changes:
        recommended_changes.append("Your resume already aligns well with this job description.")

    return {
        "overall_match": _clamp(overall),
        "keyword_match": _clamp(keyword_match),
        "skills_match": _clamp(skills_match),
        "experience_match": _clamp(experience_match),
        "education_match": _clamp(education_match),
        "matched_skills": matched_skills,
        "missing_keywords": missing_skill_keywords,
        "recommended_changes": recommended_changes,
    }


def JOB_ROLES_FLAT_SKILLS():
    flat = set()
    for role in JOB_ROLES.values():
        flat.update(role.keys())
    return flat


BULLET_VERB_UPGRADES = {
    "worked on": "developed",
    "helped with": "contributed to",
    "did": "executed",
    "made": "built",
    "used": "leveraged",
    "responsible for": "led",
}

BULLET_IMPACT_TEMPLATE = (
    "{verb} {subject}, {detail}, resulting in {impact}."
)


def improve_bullet(original):
    text = original.strip()
    if not text:
        return {"original": original, "improved": "", "note": "Please enter a bullet point first."}

    lower = text.lower()
    improved = text

    for weak, strong in BULLET_VERB_UPGRADES.items():
        if weak in lower:
            improved = re.sub(weak, strong, improved, flags=re.IGNORECASE)
            lower = improved.lower()

    # Capitalize first letter, ensure it starts with an action verb
    improved = improved[0].upper() + improved[1:] if improved else improved

    # If there is no measurable outcome, append a generic-but-honest prompt phrase
    has_number = bool(re.search(r"\d", improved))
    ends_properly = improved.rstrip().endswith((".", "!"))

    if not has_number:
        improved = improved.rstrip(". ") + ", improving efficiency and overall output quality."
    elif not ends_properly:
        improved = improved.rstrip() + "."

    # Add a technical-detail nudge if very short
    if len(improved.split()) < 8:
        improved = improved.rstrip(". ") + ", using a structured, data-driven approach."

    note = (
        "Rule-based rewrite: swapped weak verbs for stronger ones and nudged toward a "
        "measurable outcome. Double-check the numbers reflect your real impact."
    )
    return {"original": original, "improved": improved, "note": note}


def build_roadmap(role_name, missing_skills):
    steps = []
    for i, skill in enumerate(missing_skills[:4], start=1):
        steps.append({"step": i, "title": f"Strengthen {skill.title()}"})
    next_index = len(steps) + 1
    steps.append({"step": next_index, "title": "Build 2-3 portfolio projects using your strongest skills"})
    steps.append({"step": next_index + 1, "title": "Practice role-specific interview questions"})
    steps.append({"step": next_index + 2, "title": f"Apply for {role_name} internships or entry-level roles"})
    return steps


def full_analysis(parsed, target_role=None):
    ats = score_ats_compatibility(parsed)
    categories = score_categories(parsed, ats)
    checklist = build_checklist(parsed)
    recommendations = build_recommendations(parsed, checklist)

    role = target_role or guess_role_from_skills(parsed["skills"])
    gap = skill_gap_analysis(parsed["skills"], role)
    roadmap = build_roadmap(role, gap["missing_skills"])

    overall_score = round(
        categories["ats_compatibility"] * 0.35
        + categories["content_quality"] * 0.2
        + categories["skills"] * 0.2
        + categories["formatting"] * 0.15
        + categories["keyword_optimization"] * 0.1
    )

    recommended_skills = [s for s in gap["missing_skills"]][:6]

    return {
        "contact": parsed["contact"],
        "profile_role": role,
        "ats_score": overall_score,
        "resume_strength": resume_strength_label(overall_score),
        "ats_details": ats,
        "categories": categories,
        "skills_found": parsed["skills"],
        "recommended_skills": recommended_skills,
        "checklist": checklist,
        "recommendations": recommendations,
        "skill_gap": gap,
        "roadmap": roadmap,
        "available_roles": ROLE_NAMES,
    }
