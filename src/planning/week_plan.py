from math import ceil

from src.models.learner import LearnerProfile
from src.models.learning_item import LearningItem
from src.path_generator.path_builder import HOURS_PER_CONTENT_WEEK, LearningPath


def item_hours(item: LearningItem) -> float:
    return max(2.0, item.duration_weeks * HOURS_PER_CONTENT_WEEK)


def assign_calendar_weeks(items: list[LearningItem], weekly_hours: int) -> list[int]:
    weekly = max(1, weekly_hours)
    weeks: list[int] = []
    cursor = 0.0
    for item in items:
        cursor += item_hours(item)
        weeks.append(max(1, ceil(cursor / weekly)))
    return weeks


def deadline_status(profile: LearnerProfile, path: LearningPath | None) -> dict:
    deadline = None
    if profile.goals:
        deadline = profile.goals[0].deadline_weeks
    if not path:
        return {"has_deadline": bool(deadline), "deadline_weeks": deadline, "fits": True, "message": ""}
    if not deadline:
        return {
            "has_deadline": False,
            "deadline_weeks": None,
            "calendar_weeks": path.calendar_weeks,
            "fits": True,
            "message": f"No deadline set. This path takes about {path.calendar_weeks} weeks at {profile.weekly_hours}h/week.",
            "suggested_hours": None,
        }
    fits = path.calendar_weeks <= deadline
    needed = max(1, ceil(path.study_hours / deadline)) if deadline else profile.weekly_hours
    if fits:
        slack = deadline - path.calendar_weeks
        message = (
            f"On track: {path.calendar_weeks} calendar weeks vs a {deadline}-week goal "
            f"({slack} week{'s' if slack != 1 else ''} of slack) at {profile.weekly_hours}h/week."
        )
    else:
        message = (
            f"Deadline risk: this path needs ~{path.calendar_weeks} weeks but your goal is {deadline} weeks. "
            f"Raise weekly hours to about {needed}h, switch to Fast-track, or extend the deadline."
        )
    return {
        "has_deadline": True,
        "deadline_weeks": deadline,
        "calendar_weeks": path.calendar_weeks,
        "fits": fits,
        "message": message,
        "suggested_hours": needed if not fits else profile.weekly_hours,
    }


def this_week_plan(path: LearningPath, weekly_hours: int, progress: dict | None = None) -> dict:
    progress = progress or {}
    weeks = assign_calendar_weeks(path.items, weekly_hours)
    incomplete = []
    for item, week in zip(path.items, weeks):
        status = progress.get(item.id, {}).get("status")
        if status != "completed":
            incomplete.append((item, week))
    focus = incomplete[0][1] if incomplete else 1
    focus_items = [
        {
            "id": item.id,
            "title": item.title,
            "item_type": item.item_type.value,
            "hours": item_hours(item),
            "week": week,
            "description": item.description,
        }
        for item, week in zip(path.items, weeks)
        if week == focus and progress.get(item.id, {}).get("status") != "completed"
    ]
    hours = sum(x["hours"] for x in focus_items)
    return {
        "focus_week": focus,
        "weekly_hours": weekly_hours,
        "planned_hours": hours,
        "overload": hours > weekly_hours * 1.15,
        "items": focus_items,
        "guidance": (
            f"Week {focus}: {len(focus_items)} item(s), ~{hours:.0f}h planned vs {weekly_hours}h budget."
            + (" Split across two sittings if it feels heavy." if hours > weekly_hours else " Fits this week's budget.")
        ),
    }
