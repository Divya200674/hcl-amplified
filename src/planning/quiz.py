QUIZ = [
    {
        "id": "code",
        "prompt": "How comfortable are you writing code?",
        "options": [
            {"id": "none", "label": "I haven't really coded yet", "points": 0, "skills": []},
            {"id": "basics", "label": "Loops, variables, simple scripts", "points": 1, "skills": ["programming basics"]},
            {"id": "apps", "label": "I can build small apps or scripts on my own", "points": 2, "skills": ["programming basics", "problem solving"]},
        ],
    },
    {
        "id": "python",
        "prompt": "Python experience?",
        "options": [
            {"id": "none", "label": "None", "points": 0, "skills": []},
            {"id": "basics", "label": "Syntax and notebooks", "points": 1, "skills": ["python"]},
            {"id": "data", "label": "Pandas / analysis", "points": 2, "skills": ["python", "pandas"]},
        ],
    },
    {
        "id": "sql",
        "prompt": "SQL / databases?",
        "options": [
            {"id": "none", "label": "None", "points": 0, "skills": []},
            {"id": "select", "label": "SELECT and filters", "points": 1, "skills": ["sql"]},
            {"id": "joins", "label": "Joins and aggregations", "points": 2, "skills": ["sql", "database queries"]},
        ],
    },
    {
        "id": "goal",
        "prompt": "What are you aiming at?",
        "options": [
            {"id": "ds", "label": "Data scientist / analyst", "points": 0, "role": "data scientist"},
            {"id": "web", "label": "Full-stack / web", "points": 0, "role": "full-stack developer"},
            {"id": "ml", "label": "ML / AI engineer", "points": 0, "role": "ml engineer"},
            {"id": "cloud", "label": "Cloud / DevOps", "points": 0, "role": "cloud engineer"},
            {"id": "sec", "label": "Cybersecurity", "points": 0, "role": "cybersecurity analyst"},
            {"id": "mobile", "label": "Mobile apps", "points": 0, "role": "mobile developer"},
        ],
    },
    {
        "id": "hours",
        "prompt": "Hours you can study each week?",
        "options": [
            {"id": "5", "label": "About 5 hours", "hours": 5, "points": 0},
            {"id": "10", "label": "About 10 hours", "hours": 10, "points": 0},
            {"id": "15", "label": "15+ hours", "hours": 15, "points": 0},
        ],
    },
    {
        "id": "style",
        "prompt": "How do you prefer to learn?",
        "options": [
            {"id": "hands-on", "label": "Build projects", "style": "hands-on", "points": 0},
            {"id": "video", "label": "Watch explanations first", "style": "video", "points": 0},
            {"id": "reading", "label": "Docs and reading", "style": "reading", "points": 0},
        ],
    },
]


def score_quiz(answers: dict) -> dict:
    points = 0
    skills: list[str] = []
    role = "data scientist"
    hours = 10
    style = "hands-on"
    by_id = {q["id"]: q for q in QUIZ}
    for qid, opt_id in answers.items():
        question = by_id.get(qid)
        if not question:
            continue
        option = next((o for o in question["options"] if o["id"] == opt_id), None)
        if not option:
            continue
        points += int(option.get("points", 0))
        skills.extend(option.get("skills") or [])
        if option.get("role"):
            role = option["role"]
        if option.get("hours"):
            hours = int(option["hours"])
        if option.get("style"):
            style = option["style"]
    if points <= 1:
        level = "beginner"
    elif points <= 4:
        level = "intermediate"
    else:
        level = "advanced"
    return {
        "points": points,
        "skill_level": level,
        "skills": list(dict.fromkeys(skills)),
        "role": role,
        "weekly_hours": hours,
        "preferred_style": style,
    }
