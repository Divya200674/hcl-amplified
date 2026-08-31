from src.ai_assistant.llm_client import LLMClient
from src.models.learner import LearnerProfile, LearningGoal, SkillLevel
from src.profiling.profiler import parse_goal_from_text


def parse_user_goal(message: str, profile: LearnerProfile, llm: LLMClient) -> tuple[LearnerProfile, str]:
    """Parse learner goals from natural language using LLM or rules."""
    parsed = llm.parse_profile_json(message, profile.to_context_text())
    if parsed:
        profile = _merge_llm_profile(profile, parsed)
        summary = _build_summary(profile, parsed)
        return profile, summary

    profile = parse_goal_from_text(message, profile)
    summary = (
        f"I've updated your profile based on what you shared.\n\n"
        f"**Skill level:** {profile.skill_level.value.title()}\n"
        f"**Interests:** {', '.join(profile.interests) or 'General learning'}\n"
        f"**Goals:** {', '.join(g.title for g in profile.goals) or 'Exploring options'}\n\n"
        f"Head to **Learning Path** to generate your personalized roadmap!"
    )
    return profile, summary


def _merge_llm_profile(profile: LearnerProfile, data: dict) -> LearnerProfile:
    if data.get("name"):
        profile.name = data["name"]
    if data.get("interests"):
        profile.interests = list(dict.fromkeys(profile.interests + data["interests"]))
    if data.get("skill_level"):
        try:
            profile.skill_level = SkillLevel(data["skill_level"].lower())
        except ValueError:
            pass
    if data.get("current_skills"):
        profile.current_skills = list(dict.fromkeys(profile.current_skills + data["current_skills"]))
    if data.get("preferred_style"):
        profile.preferred_style = data["preferred_style"]
    if data.get("weekly_hours"):
        profile.weekly_hours = int(data["weekly_hours"])
    if data.get("goal_title"):
        profile.goals.append(
            LearningGoal(
                title=data["goal_title"],
                description=data.get("goal_description", ""),
                target_domain=data.get("target_domain", ""),
                deadline_weeks=data.get("deadline_weeks"),
            )
        )
    return profile


def _build_summary(profile: LearnerProfile, data: dict) -> str:
    goal = data.get("goal_title", "your learning journey")
    domain = data.get("target_domain", "your chosen field")
    return (
        f"Great! I've built your learner profile for **{goal}** in **{domain}**.\n\n"
        f"- **Level:** {profile.skill_level.value.title()}\n"
        f"- **Interests:** {', '.join(profile.interests) or 'Broad exploration'}\n"
        f"- **Weekly commitment:** {profile.weekly_hours} hours\n"
        f"- **Learning style:** {profile.preferred_style}\n\n"
        f"Visit **Learning Path** to generate your customized roadmap with milestones!"
    )
