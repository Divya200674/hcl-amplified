from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.career.roles import target_skills_for_profile
from src.models.learner import LearnerProfile, SkillLevel
from src.models.learning_item import LearningItem

LEVEL_ORDER = {
    SkillLevel.BEGINNER.value: 0,
    SkillLevel.INTERMEDIATE.value: 1,
    SkillLevel.ADVANCED.value: 2,
    "beginner": 0,
    "intermediate": 1,
    "advanced": 2,
}

STYLE_ITEM_HINTS = {
    "hands-on": ("project", "build", "practice", "lab", "hands"),
    "video": ("lecture", "fundamentals", "intro", "essentials"),
    "reading": ("fundamentals", "basics", "documentation", "theory"),
}


def build_profile_text(profile: LearnerProfile) -> str:
    career = " ".join(target_skills_for_profile(profile))
    parts = [
        " ".join(profile.interests),
        " ".join(profile.current_skills),
        " ".join(g.title + " " + g.target_domain + " " + g.description for g in profile.goals),
        profile.skill_level.value,
        profile.preferred_style,
        career,
    ]
    return " ".join(p for p in parts if p)


def content_similarity(profile: LearnerProfile, items: list[LearningItem]) -> list[float]:
    if not items:
        return []
    corpus = [build_profile_text(profile)] + [item.searchable_text() for item in items]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=2000, ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    similarities = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return similarities.tolist()


def skill_gap_score(profile: LearnerProfile, item: LearningItem) -> float:
    if not item.skills_taught:
        return 0.3
    missing = [s for s in item.skills_taught if s.lower() not in {c.lower() for c in profile.current_skills}]
    return len(missing) / len(item.skills_taught)


def career_skill_score(profile: LearnerProfile, item: LearningItem) -> float:
    targets = {s.lower() for s in target_skills_for_profile(profile)}
    if not targets or not item.skills_taught:
        return 0.4
    overlap = [s for s in item.skills_taught if s.lower() in targets]
    owned = {c.lower() for c in profile.current_skills}
    useful = [s for s in overlap if s.lower() not in owned]
    return min(1.0, (len(useful) / max(1, min(4, len(targets)))) + 0.15 * len(overlap))


def domain_fit_score(profile: LearnerProfile, item: LearningItem) -> float:
    domains = [g.target_domain.lower() for g in profile.goals if g.target_domain]
    domains += [i.lower() for i in profile.interests]
    item_domain = item.domain.lower()
    if any(item_domain in d or d in item_domain for d in domains if d):
        return 1.0
    return 0.25


def style_fit_score(profile: LearnerProfile, item: LearningItem) -> float:
    hints = STYLE_ITEM_HINTS.get(profile.preferred_style, ())
    blob = f"{item.title} {item.description} {item.item_type.value}".lower()
    if profile.preferred_style == "hands-on" and item.item_type.value == "project":
        return 1.0
    if any(h in blob for h in hints):
        return 0.85
    return 0.5


def level_fit_score(profile: LearnerProfile, item: LearningItem) -> float:
    user_level = LEVEL_ORDER.get(profile.skill_level.value, 1)
    item_level = LEVEL_ORDER.get(item.level.lower(), 1)
    diff = abs(user_level - item_level)
    if diff == 0:
        return 1.0
    if item_level == user_level + 1:
        return 0.72
    if diff == 1:
        return 0.55
    return 0.18


def time_fit_score(profile: LearnerProfile, item: LearningItem) -> float:
    hours = max(1, profile.weekly_hours)
    item_hours = max(2.0, item.duration_weeks * 8)
    weeks_needed = item_hours / hours
    if weeks_needed <= 3:
        return 1.0
    if weeks_needed <= 6:
        return 0.7
    return 0.4


def prerequisites_met(profile: LearnerProfile, item: LearningItem, unlocked: set[str] | None = None) -> bool:
    completed = set(profile.completed_items)
    if unlocked:
        completed |= unlocked
    return all(p in completed for p in item.prerequisites)


def feedback_boost(profile: LearnerProfile, item: LearningItem) -> float:
    score = profile.feedback_scores.get(item.id, 0)
    if score > 0:
        return 1.0
    if score < 0:
        return 0.0
    return 0.5
