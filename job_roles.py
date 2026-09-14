"""
job_roles.py

A local, hand-curated database of target job roles and the skills that
matter for each one. No external API is used here — this is the
rule-based backbone that lets the whole app run completely offline.

Each role maps to a dict of skill -> importance weight (1-10).
Weights feed into the skill-gap percentages and job-match scores so
that core skills count for more than nice-to-haves.
"""

JOB_ROLES = {
    "Data Analyst": {
        "python": 8, "sql": 10, "excel": 9, "power bi": 8,
        "statistics": 8, "pandas": 8, "data visualization": 7,
        "tableau": 6, "numpy": 5, "communication": 5,
    },
    "Data Scientist": {
        "python": 10, "machine learning": 10, "statistics": 9,
        "sql": 8, "pandas": 8, "numpy": 7, "scikit-learn": 8,
        "data visualization": 6, "deep learning": 6, "r": 4,
    },
    "AI/ML Engineer": {
        "python": 10, "machine learning": 10, "deep learning": 9,
        "tensorflow": 8, "pytorch": 8, "statistics": 7,
        "numpy": 6, "pandas": 6, "nlp": 5, "computer vision": 5,
    },
    "Software Engineer": {
        "python": 7, "java": 6, "javascript": 7, "git": 8,
        "data structures": 9, "algorithms": 9, "sql": 6,
        "rest api": 6, "system design": 5, "testing": 5,
    },
    "Cloud Engineer": {
        "aws": 9, "azure": 6, "docker": 8, "kubernetes": 8,
        "linux": 7, "networking": 6, "ci/cd": 7, "terraform": 5,
        "python": 5, "bash": 5,
    },
    "Biomedical Engineer": {
        "matlab": 7, "python": 6, "signal processing": 8,
        "biomechanics": 7, "cad": 6, "medical imaging": 7,
        "statistics": 5, "regulatory knowledge": 4,
    },
    "Business Analyst": {
        "sql": 7, "excel": 9, "power bi": 7, "communication": 8,
        "requirements gathering": 8, "data visualization": 6,
        "statistics": 5, "process mapping": 6,
    },
    "Product Analyst": {
        "sql": 8, "excel": 6, "python": 5, "a/b testing": 7,
        "data visualization": 7, "communication": 6,
        "statistics": 6, "product sense": 6,
    },
}

# Flat set of every recognised skill keyword, used by the resume parser
# to scan free text for skill mentions.
ALL_KNOWN_SKILLS = sorted({skill for role in JOB_ROLES.values() for skill in role})

ROLE_NAMES = list(JOB_ROLES.keys())


def get_required_skills(role_name):
    """Return the skill->weight dict for a role, or {} if unknown."""
    return JOB_ROLES.get(role_name, {})


def guess_role_from_skills(found_skills):
    """Pick the role with the highest weighted overlap against found skills."""
    found = {s.lower() for s in found_skills}
    best_role, best_score = ROLE_NAMES[0], -1
    for role, required in JOB_ROLES.items():
        score = sum(weight for skill, weight in required.items() if skill in found)
        if score > best_score:
            best_role, best_score = role, score
    return best_role
