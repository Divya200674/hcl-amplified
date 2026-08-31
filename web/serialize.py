from src.ai_assistant.explainer import explain_recommendation
from src.career.roles import target_skills_for_profile
from src.models.learner import LearnerProfile
from src.path_generator.path_builder import LearningPath
from src.planning.week_plan import assign_calendar_weeks, deadline_status, this_week_plan
from web.state import LLM


def profile_dict(profile: LearnerProfile | None) -> dict | None:
    if not profile:
        return None
    return {
        "name": profile.name,
        "skill_level": profile.skill_level.value,
        "interests": profile.interests,
        "current_skills": profile.current_skills,
        "completed_items": profile.completed_items,
        "preferred_style": profile.preferred_style,
        "weekly_hours": profile.weekly_hours,
        "goals": [g.model_dump() for g in profile.goals],
        "target_skills": target_skills_for_profile(profile),
    }


def path_dict(
    profile: LearnerProfile | None,
    path: LearningPath | None,
    progress: dict | None = None,
) -> dict | None:
    if not path:
        return None
    weeks = assign_calendar_weeks(path.items, profile.weekly_hours if profile else 10)
    items = []
    for item, week in zip(path.items, weeks):
        score = path.scores.get(item.id, 0)
        breakdown = path.breakdowns.get(item.id, {})
        items.append(
            {
                "id": item.id,
                "title": item.title,
                "domain": item.domain,
                "level": item.level,
                "duration_weeks": item.duration_weeks,
                "skills_taught": item.skills_taught,
                "prerequisites": item.prerequisites,
                "description": item.description,
                "item_type": item.item_type.value,
                "score": round(score, 4),
                "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
                "calendar_week": week,
                "explanation": explain_recommendation(item, profile, score, LLM, breakdown)
                if profile
                else "",
            }
        )
    payload = {
        "items": items,
        "milestones": [
            {"week": m.week, "title": m.title, "item_id": m.item_id, "item_type": m.item_type}
            for m in path.milestones
        ],
        "calendar_weeks": path.calendar_weeks,
        "study_hours": path.study_hours,
        "total_weeks": path.total_weeks,
        "intensity": path.intensity,
        "coverage": path.coverage,
        "count": len(path.items),
    }
    if profile:
        payload["deadline"] = deadline_status(profile, path)
        payload["this_week"] = this_week_plan(path, profile.weekly_hours, progress or {})
    return payload


def profile_dict(profile: LearnerProfile | None) -> dict | None:
    if not profile:
        return None
    return {
        "name": profile.name,
        "skill_level": profile.skill_level.value,
        "interests": profile.interests,
        "current_skills": profile.current_skills,
        "completed_items": profile.completed_items,
        "preferred_style": profile.preferred_style,
        "weekly_hours": profile.weekly_hours,
        "goals": [g.model_dump() for g in profile.goals],
        "target_skills": target_skills_for_profile(profile),
    }


def path_dict(profile: LearnerProfile | None, path: LearningPath | None) -> dict | None:
    if not path:
        return None
    items = []
    for item in path.items:
        score = path.scores.get(item.id, 0)
        breakdown = path.breakdowns.get(item.id, {})
        items.append(
            {
                "id": item.id,
                "title": item.title,
                "domain": item.domain,
                "level": item.level,
                "duration_weeks": item.duration_weeks,
                "skills_taught": item.skills_taught,
                "prerequisites": item.prerequisites,
                "description": item.description,
                "item_type": item.item_type.value,
                "score": round(score, 4),
                "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
                "explanation": explain_recommendation(item, profile, score, LLM, breakdown)
                if profile
                else "",
            }
        )
    return {
        "items": items,
        "milestones": [
            {"week": m.week, "title": m.title, "item_id": m.item_id, "item_type": m.item_type}
            for m in path.milestones
        ],
        "calendar_weeks": path.calendar_weeks,
        "study_hours": path.study_hours,
        "total_weeks": path.total_weeks,
        "intensity": path.intensity,
        "coverage": path.coverage,
        "count": len(path.items),
    }
