"""Career role maps used for skill-gap targeting and onboarding templates."""

from src.models.learner import LearnerProfile, LearningGoal, SkillLevel

CAREER_ROLES: dict[str, dict] = {
    "data scientist": {
        "domain": "Data Science",
        "interests": ["data science", "artificial intelligence"],
        "skills": [
            "python", "statistics", "pandas", "sql", "data visualization",
            "supervised learning", "model evaluation", "scikit-learn",
        ],
        "prompt": "I know Python basics and want to become a data scientist in 6 months, 10 hours per week, hands-on.",
    },
    "full-stack developer": {
        "domain": "Web Development",
        "interests": ["web development"],
        "skills": [
            "html", "css", "javascript", "react", "nodejs", "rest api", "full stack",
        ],
        "prompt": "I'm a beginner interested in web development and want to become a full-stack developer in 5 months.",
    },
    "ml engineer": {
        "domain": "Artificial Intelligence",
        "interests": ["artificial intelligence", "data science"],
        "skills": [
            "python", "supervised learning", "deep learning", "mlops",
            "model deployment", "docker",
        ],
        "prompt": "I have intermediate ML skills and want to become an ML engineer focusing on deployment.",
    },
    "cloud engineer": {
        "domain": "Cloud Computing",
        "interests": ["cloud computing"],
        "skills": ["aws", "docker", "kubernetes", "ci/cd", "cloud computing"],
        "prompt": "Help me transition to cloud computing with AWS, I can study 8 hours per week.",
    },
    "cybersecurity analyst": {
        "domain": "Cybersecurity",
        "interests": ["cybersecurity"],
        "skills": ["cybersecurity", "network security", "penetration testing"],
        "prompt": "I am a beginner and want to become a cybersecurity analyst with hands-on labs.",
    },
    "mobile developer": {
        "domain": "Mobile Development",
        "interests": ["mobile development"],
        "skills": ["flutter", "dart", "mobile development", "android"],
        "prompt": "I know JavaScript and want to become a mobile developer using Flutter.",
    },
}

ROLE_ALIASES = {
    "data science": "data scientist",
    "data analyst": "data scientist",
    "web developer": "full-stack developer",
    "fullstack": "full-stack developer",
    "full stack": "full-stack developer",
    "machine learning engineer": "ml engineer",
    "ai engineer": "ml engineer",
    "devops": "cloud engineer",
    "aws": "cloud engineer",
    "security": "cybersecurity analyst",
    "android": "mobile developer",
    "ios": "mobile developer",
}


def detect_role(text: str) -> str | None:
    lower = text.lower()
    for role in CAREER_ROLES:
        if role in lower:
            return role
    for alias, role in ROLE_ALIASES.items():
        if alias in lower:
            return role
    return None


def target_skills_for_profile(profile: LearnerProfile) -> list[str]:
    skills: list[str] = []
    texts = [g.title + " " + g.target_domain for g in profile.goals] + profile.interests
    blob = " ".join(texts).lower()
    role = detect_role(blob)
    if role:
        skills.extend(CAREER_ROLES[role]["skills"])
    return list(dict.fromkeys(skills))


def apply_role_template(profile: LearnerProfile, role_key: str) -> LearnerProfile:
    role = CAREER_ROLES[role_key]
    profile.interests = list(dict.fromkeys(profile.interests + role["interests"]))
    if not profile.goals:
        profile.goals.append(
            LearningGoal(
                title=role_key.title(),
                description=f"Become a {role_key}",
                target_domain=role["domain"],
                deadline_weeks=24,
            )
        )
    else:
        profile.goals[0].target_domain = profile.goals[0].target_domain or role["domain"]
    if profile.skill_level == SkillLevel.BEGINNER and "python" in role["skills"]:
        if "python" not in profile.current_skills:
            pass
    return profile
