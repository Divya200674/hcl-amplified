from dataclasses import dataclass, field
from math import ceil

import networkx as nx

from src.models.learner import LearnerProfile
from src.models.learning_item import ItemType, LearningItem
from src.recommendation.hybrid_engine import HybridRecommendationEngine, ScoredItem

HOURS_PER_CONTENT_WEEK = 8

INTENSITY_CONFIG = {
    "fast-track": {"courses": 5, "projects": 2, "assessments": 1},
    "balanced": {"courses": 7, "projects": 3, "assessments": 2},
    "deep": {"courses": 9, "projects": 3, "assessments": 3},
}


@dataclass
class Milestone:
    week: int
    title: str
    item_id: str
    item_type: str


@dataclass
class LearningPath:
    items: list[LearningItem] = field(default_factory=list)
    milestones: list[Milestone] = field(default_factory=list)
    total_weeks: float = 0.0
    calendar_weeks: int = 0
    study_hours: float = 0.0
    scores: dict[str, float] = field(default_factory=dict)
    breakdowns: dict[str, dict[str, float]] = field(default_factory=dict)
    intensity: str = "balanced"
    coverage: float = 0.0

    def titles(self) -> list[str]:
        return [item.title for item in self.items]


class LearningPathGenerator:
    def __init__(self) -> None:
        self.engine = HybridRecommendationEngine()

    def generate(
        self,
        profile: LearnerProfile,
        catalog: list[LearningItem],
        intensity: str = "balanced",
    ) -> LearningPath:
        cfg = INTENSITY_CONFIG.get(intensity, INTENSITY_CONFIG["balanced"])
        by_id = {item.id: item for item in catalog}

        scored_all = self.engine.recommend(profile, catalog, top_k=len(catalog))
        score_map = {s.item.id: s.score for s in scored_all}
        breakdown_map = {s.item.id: s.breakdown for s in scored_all}

        courses = [s.item for s in scored_all if s.item.item_type == ItemType.COURSE][: cfg["courses"] + 4]
        projects = [s.item for s in scored_all if s.item.item_type == ItemType.PROJECT][: cfg["projects"] + 2]
        assessments = [s.item for s in scored_all if s.item.item_type == ItemType.ASSESSMENT][: cfg["assessments"] + 2]

        selected_ids = {c.id for c in courses[: cfg["courses"]]}
        selected_ids |= {p.id for p in projects[: cfg["projects"]]}
        selected_ids |= {a.id for a in assessments[: cfg["assessments"]]}

        selected_ids = self._inject_prerequisites(selected_ids, by_id)
        ordered = self._topological_order(selected_ids, by_id, score_map)
        ordered = self._fit_time_budget(ordered, profile)
        ordered = self._prefer_style_order(ordered, profile)

        study_hours = sum(max(2.0, i.duration_weeks * HOURS_PER_CONTENT_WEEK) for i in ordered)
        weekly = max(1, profile.weekly_hours)
        calendar_weeks = max(1, ceil(study_hours / weekly))

        deadline = None
        if profile.goals:
            deadline = profile.goals[0].deadline_weeks
        if deadline and calendar_weeks > deadline:
            ordered = self._trim_to_deadline(ordered, profile, deadline)
            study_hours = sum(max(2.0, i.duration_weeks * HOURS_PER_CONTENT_WEEK) for i in ordered)
            calendar_weeks = max(1, ceil(study_hours / weekly))

        milestones: list[Milestone] = []
        hour_cursor = 0.0
        for item in ordered:
            hour_cursor += max(2.0, item.duration_weeks * HOURS_PER_CONTENT_WEEK)
            week_mark = max(1, ceil(hour_cursor / weekly))
            if item.item_type in (ItemType.ASSESSMENT, ItemType.PROJECT):
                milestones.append(
                    Milestone(
                        week=week_mark,
                        title=f"Milestone: {item.title}",
                        item_id=item.id,
                        item_type=item.item_type.value,
                    )
                )

        from src.career.roles import target_skills_for_profile

        targets = {s.lower() for s in target_skills_for_profile(profile)}
        taught = {s.lower() for item in ordered for s in item.skills_taught}
        coverage = (len(targets & taught) / len(targets)) if targets else 0.75

        return LearningPath(
            items=ordered,
            milestones=milestones,
            total_weeks=sum(i.duration_weeks for i in ordered),
            calendar_weeks=calendar_weeks,
            study_hours=study_hours,
            scores=score_map,
            breakdowns=breakdown_map,
            intensity=intensity,
            coverage=coverage,
        )

    def alternatives(
        self,
        profile: LearnerProfile,
        catalog: list[LearningItem],
        path: LearningPath,
        item_id: str,
        limit: int = 4,
    ) -> list[ScoredItem]:
        current = next((i for i in path.items if i.id == item_id), None)
        if not current:
            return []
        in_path = {i.id for i in path.items}
        scored = self.engine.recommend(profile, catalog, top_k=len(catalog))
        alts = [
            s
            for s in scored
            if s.item.id not in in_path
            and s.item.item_type == current.item_type
            and s.item.id != item_id
        ]
        same_domain = [s for s in alts if s.item.domain == current.domain]
        pool = same_domain or alts
        return pool[:limit]

    def swap_item(
        self,
        profile: LearnerProfile,
        catalog: list[LearningItem],
        path: LearningPath,
        old_id: str,
        new_id: str,
    ) -> LearningPath:
        by_id = {item.id: item for item in catalog}
        if new_id not in by_id:
            raise ValueError("Unknown replacement")
        selected = {i.id for i in path.items}
        if old_id in selected:
            selected.remove(old_id)
        selected.add(new_id)
        selected = self._inject_prerequisites(selected, by_id)
        ordered = self._topological_order(selected, by_id, path.scores)
        ordered = self._prefer_style_order(ordered, profile)
        return self._finalize(ordered, profile, path.scores, path.breakdowns, path.intensity)

    def _finalize(
        self,
        ordered: list[LearningItem],
        profile: LearnerProfile,
        score_map: dict[str, float],
        breakdown_map: dict[str, dict[str, float]],
        intensity: str,
    ) -> LearningPath:
        study_hours = sum(max(2.0, i.duration_weeks * HOURS_PER_CONTENT_WEEK) for i in ordered)
        weekly = max(1, profile.weekly_hours)
        calendar_weeks = max(1, ceil(study_hours / weekly))
        milestones: list[Milestone] = []
        hour_cursor = 0.0
        for item in ordered:
            hour_cursor += max(2.0, item.duration_weeks * HOURS_PER_CONTENT_WEEK)
            week_mark = max(1, ceil(hour_cursor / weekly))
            if item.item_type in (ItemType.ASSESSMENT, ItemType.PROJECT):
                milestones.append(
                    Milestone(
                        week=week_mark,
                        title=f"Milestone: {item.title}",
                        item_id=item.id,
                        item_type=item.item_type.value,
                    )
                )
        from src.career.roles import target_skills_for_profile

        targets = {s.lower() for s in target_skills_for_profile(profile)}
        taught = {s.lower() for item in ordered for s in item.skills_taught}
        coverage = (len(targets & taught) / len(targets)) if targets else 0.75
        return LearningPath(
            items=ordered,
            milestones=milestones,
            total_weeks=sum(i.duration_weeks for i in ordered),
            calendar_weeks=calendar_weeks,
            study_hours=study_hours,
            scores=score_map,
            breakdowns=breakdown_map,
            intensity=intensity,
            coverage=coverage,
        )

    def compare_intensities(
        self, profile: LearnerProfile, catalog: list[LearningItem]
    ) -> dict[str, LearningPath]:
        return {
            key: self.generate(profile, catalog, intensity=key)
            for key in INTENSITY_CONFIG
        }

    def _inject_prerequisites(self, selected: set[str], by_id: dict[str, LearningItem]) -> set[str]:
        changed = True
        while changed:
            changed = False
            for item_id in list(selected):
                item = by_id.get(item_id)
                if not item:
                    continue
                for prereq in item.prerequisites:
                    if prereq in by_id and prereq not in selected:
                        selected.add(prereq)
                        changed = True
        return selected

    def _topological_order(
        self,
        selected: set[str],
        by_id: dict[str, LearningItem],
        score_map: dict[str, float],
    ) -> list[LearningItem]:
        graph = nx.DiGraph()
        for item_id in selected:
            item = by_id.get(item_id)
            if not item:
                continue
            graph.add_node(item_id, data=item)
            for prereq in item.prerequisites:
                if prereq in selected:
                    graph.add_edge(prereq, item_id)

        if graph.number_of_nodes() == 0:
            return []
        if not nx.is_directed_acyclic_graph(graph):
            items = [by_id[i] for i in selected if i in by_id]
            items.sort(key=lambda x: score_map.get(x.id, 0), reverse=True)
            return items

        ordered_ids = list(nx.topological_sort(graph))
        return [graph.nodes[n]["data"] for n in ordered_ids]

    def _fit_time_budget(self, items: list[LearningItem], profile: LearnerProfile) -> list[LearningItem]:
        deadline = None
        if profile.goals:
            deadline = profile.goals[0].deadline_weeks
        if not deadline:
            return items
        weekly = max(1, profile.weekly_hours)
        budget_hours = deadline * weekly
        kept: list[LearningItem] = []
        used = 0.0
        for item in items:
            cost = max(2.0, item.duration_weeks * HOURS_PER_CONTENT_WEEK)
            if used + cost <= budget_hours * 1.08 or item.item_type == ItemType.COURSE and len(kept) < 3:
                kept.append(item)
                used += cost
        return kept or items[:4]

    def _trim_to_deadline(
        self, items: list[LearningItem], profile: LearnerProfile, deadline: int
    ) -> list[LearningItem]:
        weekly = max(1, profile.weekly_hours)
        budget = deadline * weekly
        kept: list[LearningItem] = []
        used = 0.0
        for item in items:
            cost = max(2.0, item.duration_weeks * HOURS_PER_CONTENT_WEEK)
            if used + cost <= budget:
                kept.append(item)
                used += cost
        return kept or items[:3]

    def _prefer_style_order(self, items: list[LearningItem], profile: LearnerProfile) -> list[LearningItem]:
        if profile.preferred_style != "hands-on":
            return items
        courses = [i for i in items if i.item_type == ItemType.COURSE]
        projects = [i for i in items if i.item_type == ItemType.PROJECT]
        assessments = [i for i in items if i.item_type == ItemType.ASSESSMENT]
        mixed: list[LearningItem] = []
        pi = ai = 0
        for idx, course in enumerate(courses):
            mixed.append(course)
            if (idx + 1) % 2 == 0 and pi < len(projects):
                mixed.append(projects[pi])
                pi += 1
            if (idx + 1) % 3 == 0 and ai < len(assessments):
                mixed.append(assessments[ai])
                ai += 1
        mixed.extend(projects[pi:])
        mixed.extend(assessments[ai:])
        return mixed or items
