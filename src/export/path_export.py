from src.models.learner import LearnerProfile
from src.path_generator.path_builder import LearningPath


def path_to_markdown(profile: LearnerProfile, path: LearningPath) -> str:
    goals = ", ".join(g.title for g in profile.goals) or "Personalized learning"
    lines = [
        f"# Learning Path: {goals}",
        "",
        f"- **Learner:** {profile.name}",
        f"- **Level:** {profile.skill_level.value.title()}",
        f"- **Weekly hours:** {profile.weekly_hours}",
        f"- **Style:** {profile.preferred_style}",
        f"- **Calendar duration:** {path.calendar_weeks} weeks",
        f"- **Study hours:** {path.study_hours:.0f}",
        f"- **Intensity:** {path.intensity.title()}",
        "",
        "## Roadmap",
        "",
    ]
    week = 0
    for i, item in enumerate(path.items, start=1):
        week += max(1, int(round(item.duration_weeks)))
        score = path.scores.get(item.id, 0)
        lines.append(
            f"### {i}. {item.title} ({item.item_type.value.title()})"
        )
        lines.append(f"- Domain: {item.domain} | Level: {item.level} | ~Week {week}")
        lines.append(f"- Match score: {score:.0%}")
        lines.append(f"- Skills: {', '.join(item.skills_taught) or '—'}")
        lines.append(f"- {item.description}")
        lines.append("")
    if path.milestones:
        lines.append("## Milestones")
        for ms in path.milestones:
            lines.append(f"- Week {ms.week}: {ms.title}")
    return "\n".join(lines)
