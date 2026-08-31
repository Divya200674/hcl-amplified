from dataclasses import dataclass

from src.models.learner import LearnerProfile
from src.models.learning_item import ItemType, LearningItem
from src.recommendation.content_based import (
    career_skill_score,
    content_similarity,
    domain_fit_score,
    feedback_boost,
    level_fit_score,
    skill_gap_score,
    style_fit_score,
    time_fit_score,
)


@dataclass
class ScoredItem:
    item: LearningItem
    score: float
    breakdown: dict[str, float]


class HybridRecommendationEngine:
    WEIGHTS = {
        "content": 0.28,
        "career": 0.18,
        "skill_gap": 0.16,
        "domain": 0.12,
        "level_fit": 0.10,
        "style": 0.06,
        "time": 0.05,
        "popularity": 0.03,
        "feedback": 0.02,
    }

    def recommend(
        self,
        profile: LearnerProfile,
        catalog: list[LearningItem],
        top_k: int = 20,
        item_types: list[ItemType] | None = None,
        require_prereqs: bool = False,
        unlocked: set[str] | None = None,
    ) -> list[ScoredItem]:
        candidates = []
        for item in catalog:
            if item.id in profile.completed_items:
                continue
            if item_types is not None and item.item_type not in item_types:
                continue
            if require_prereqs:
                from src.recommendation.content_based import prerequisites_met

                if not prerequisites_met(profile, item, unlocked):
                    continue
            candidates.append(item)

        if not candidates:
            return []

        sims = content_similarity(profile, candidates)
        scored: list[ScoredItem] = []
        for idx, item in enumerate(candidates):
            breakdown = {
                "content": float(sims[idx]),
                "career": career_skill_score(profile, item),
                "skill_gap": skill_gap_score(profile, item),
                "domain": domain_fit_score(profile, item),
                "level_fit": level_fit_score(profile, item),
                "style": style_fit_score(profile, item),
                "time": time_fit_score(profile, item),
                "popularity": item.popularity,
                "feedback": feedback_boost(profile, item),
            }
            total = sum(breakdown[k] * self.WEIGHTS[k] for k in self.WEIGHTS)
            scored.append(ScoredItem(item=item, score=total, breakdown=breakdown))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]
