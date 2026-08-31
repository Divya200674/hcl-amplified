import json
import re
from pathlib import Path

from src.career.roles import apply_role_template, detect_role
from src.models.learner import LearnerProfile, LearningGoal, SkillLevel

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"

DOMAIN_KEYWORDS = {
    "data science": ["data", "ml", "machine learning", "analytics", "statistics", "pandas"],
    "web development": ["web", "frontend", "backend", "react", "javascript", "html", "css"],
    "cloud computing": ["cloud", "aws", "azure", "devops", "kubernetes", "docker"],
    "cybersecurity": ["security", "cyber", "ethical hacking", "network security"],
    "artificial intelligence": ["ai", "deep learning", "nlp", "computer vision", "llm"],
    "mobile development": ["mobile", "android", "ios", "flutter", "react native"],
}

STYLE_KEYWORDS = {
    "video": ["video", "lecture", "watch"],
    "hands-on": ["project", "hands-on", "practice", "build"],
    "reading": ["book", "reading", "documentation", "text"],
}


def _load_catalog(filename: str) -> list[dict]:
    path = DATA_DIR / filename
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_all_items():
    from src.models.learning_item import LearningItem

    items: list[LearningItem] = []
    for filename in ("courses.json", "projects.json", "assessments.json"):
        for raw in _load_catalog(filename):
            raw.setdefault("item_type", filename.replace(".json", "").rstrip("s"))
            if raw["item_type"] == "course":
                raw["item_type"] = "course"
            elif raw["item_type"] == "project":
                raw["item_type"] = "project"
            else:
                raw["item_type"] = "assessment"
            items.append(LearningItem(**raw))
    return items


def parse_goal_from_text(text: str, profile: LearnerProfile) -> LearnerProfile:
    """Rule-based NLP parser when LLM is unavailable."""
    lower = text.lower()

    level_map = {
        "beginner": SkillLevel.BEGINNER,
        "basic": SkillLevel.BEGINNER,
        "new to": SkillLevel.BEGINNER,
        "intermediate": SkillLevel.INTERMEDIATE,
        "some experience": SkillLevel.INTERMEDIATE,
        "advanced": SkillLevel.ADVANCED,
        "expert": SkillLevel.ADVANCED,
    }
    for keyword, level in level_map.items():
        if keyword in lower:
            profile.skill_level = level
            break

    interests: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in lower for kw in keywords) or domain in lower:
            interests.append(domain)
    if interests:
        profile.interests = list(dict.fromkeys(profile.interests + interests))

    for style, keywords in STYLE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            profile.preferred_style = style
            break

    new_goal = None
    months_match = re.search(r"(\d+)\s*(?:month|months)", lower)
    weeks_only = re.search(r"(\d+)\s*(?:week|weeks)", lower)
    if months_match:
        new_goal = LearningGoal(
            title=_extract_goal_title(text),
            description=text[:200],
            target_domain=interests[0] if interests else "general",
            deadline_weeks=int(months_match.group(1)) * 4,
        )
    elif weeks_only:
        new_goal = LearningGoal(
            title=_extract_goal_title(text),
            description=text[:200],
            target_domain=interests[0] if interests else "general",
            deadline_weeks=int(weeks_only.group(1)),
        )
    elif "become" in lower or "want to" in lower or "goal" in lower:
        new_goal = LearningGoal(
            title=_extract_goal_title(text),
            description=text[:200],
            target_domain=interests[0] if interests else "general",
        )
    if new_goal:
        profile.goals = [new_goal]

    skills = re.findall(r"know(?:s)?\s+([\w\s\+#]+?)(?:\.|,|$|and)", lower)
    for skill in skills:
        profile.current_skills.append(skill.strip())

    hours_match = re.search(r"(\d+)\s*(?:hour|hours)\s*(?:per|a)\s*week", lower)
    if hours_match:
        profile.weekly_hours = int(hours_match.group(1))

    role = detect_role(text)
    if role:
        profile = apply_role_template(profile, role)
        if not any(g.target_domain for g in profile.goals) and interests:
            profile.goals[-1].target_domain = interests[0]

    return profile


def _extract_goal_title(text: str) -> str:
    lower = text.lower()
    become_match = re.search(r"(?:want to|wanna|wish to)\s+(?:become|be)\s+(?:a\s+)?(.+?)(?:\.|,|$)", lower)
    if become_match:
        return become_match.group(1).strip().title()
    if len(text) <= 80:
        return text.strip()
    return text[:77].strip() + "..."


def update_profile_from_completion(profile: LearnerProfile, item_id: str, items_by_id: dict) -> LearnerProfile:
    if item_id not in profile.completed_items:
        profile.completed_items.append(item_id)
    item = items_by_id.get(item_id)
    if item:
        for skill in item.skills_taught:
            if skill not in profile.current_skills:
                profile.current_skills.append(skill)
    return profile


def apply_feedback(profile: LearnerProfile, item_id: str, score: int) -> LearnerProfile:
    profile.feedback_scores[item_id] = score
    return profile
