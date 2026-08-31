from src.ai_assistant.llm_client import LLMClient
from src.career.roles import target_skills_for_profile
from src.models.learner import LearnerProfile
from src.models.learning_item import LearningItem


def explain_recommendation(
    item: LearningItem,
    profile: LearnerProfile,
    score: float,
    llm: LLMClient,
    breakdown: dict[str, float] | None = None,
) -> str:
    if llm.available:
        system = (
            "You are a learning advisor. Explain in 3-4 concise bullet points why "
            "this learning resource was recommended. Be specific about skill gaps and goals."
        )
        user = (
            f"Learner profile:\n{profile.to_context_text()}\n\n"
            f"Recommended item: {item.title}\n"
            f"Type: {item.item_type.value}\n"
            f"Skills taught: {', '.join(item.skills_taught)}\n"
            f"Level: {item.level}\n"
            f"Description: {item.description}\n"
            f"Match score: {score:.2f}"
        )
        response = llm.chat(system, user)
        if response and not response.lower().startswith("i encountered an issue"):
            return response

    return _rule_based_explanation(item, profile, score, breakdown)


def answer_learner_query(
    query: str,
    profile: LearnerProfile,
    path_titles: list[str],
    llm: LLMClient,
    extra_context: str = "",
) -> str:
    if llm.available:
        system = (
            "You are an AI learning assistant. Answer the learner's question using "
            "their profile and current learning path. Be helpful, concise, and actionable."
        )
        user = (
            f"Profile:\n{profile.to_context_text()}\n\n"
            f"Current learning path: {', '.join(path_titles) or 'Not generated yet'}\n"
            f"{extra_context}\n\n"
            f"Question: {query}"
        )
        response = llm.chat(system, user)
        if response and not response.lower().startswith("i encountered an issue"):
            return response

    return _fallback_answer(query, profile, path_titles)


def _rule_based_explanation(
    item: LearningItem,
    profile: LearnerProfile,
    score: float,
    breakdown: dict[str, float] | None = None,
) -> str:
    reasons = []
    goal_domains = [g.target_domain.lower() for g in profile.goals if g.target_domain]
    interests = [i.lower() for i in profile.interests]
    if any(item.domain.lower() in d or d in item.domain.lower() for d in goal_domains + interests if d):
        reasons.append(f"Aligns with your **{item.domain}** goal and interests.")

    owned = {s.lower() for s in profile.current_skills}
    missing = [s for s in item.skills_taught if s.lower() not in owned]
    if missing:
        reasons.append(f"Closes skill gaps: **{', '.join(missing[:4])}**.")

    career = {s.lower() for s in target_skills_for_profile(profile)}
    career_hits = [s for s in item.skills_taught if s.lower() in career]
    if career_hits:
        reasons.append(f"Maps to your target career skills: **{', '.join(career_hits[:3])}**.")

    if item.level == profile.skill_level.value:
        reasons.append(f"Difficulty matches your **{profile.skill_level.value}** level.")
    elif item.level == "intermediate" and profile.skill_level.value == "beginner":
        reasons.append("Stretches you one level up after foundations are in place.")

    if profile.preferred_style == "hands-on" and item.item_type.value == "project":
        reasons.append("Fits your **hands-on** preference with a build-focused project.")

    prereqs_met = all(p in profile.completed_items for p in item.prerequisites)
    if item.prerequisites and prereqs_met:
        reasons.append("Prerequisites are already covered in your profile or path.")
    elif item.prerequisites:
        reasons.append(f"Placed after prerequisites: **{', '.join(item.prerequisites)}**.")

    if breakdown:
        top = sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True)[:2]
        reasons.append("Top scoring signals: " + ", ".join(f"**{k}** ({v:.0%})" for k, v in top) + ".")

    if not reasons:
        reasons.append(f"Strong overall match (**{score:.0%}**) for your stated goal.")
    return "\n".join(f"- {r}" for r in reasons)


def _fallback_answer(query: str, profile: LearnerProfile, path_titles: list[str]) -> str:
    lower = query.lower()
    if "next" in lower or "start" in lower:
        if path_titles:
            return (
                f"Start with **{path_titles[0]}**. Complete it before moving on so "
                f"prerequisites stay valid."
            )
        return "Generate your learning path first from the **Learning Path** page."
    if "skill" in lower or "gap" in lower:
        skills = ", ".join(profile.current_skills) or "none recorded yet"
        targets = ", ".join(target_skills_for_profile(profile)) or "your selected career skills"
        return f"Current skills: **{skills}**. Target career skills: **{targets}**."
    if "hour" in lower or "time" in lower or "week" in lower:
        return (
            f"You set **{profile.weekly_hours} hours/week**. The path calendar is packed "
            f"to that budget (and any deadline on your goal)."
        )
    if "why" in lower:
        return (
            "Each item is scored with TF-IDF similarity, career-skill coverage, skill-gap, "
            "domain fit, level, learning style, time, popularity, and your 👍/👎 feedback."
        )
    if "goal" in lower:
        goals = ", ".join(g.title for g in profile.goals) or "not set"
        return f"Your stated goals: **{goals}**. The roadmap is sequenced to reach them."
    if path_titles:
        preview = ", ".join(path_titles[:4])
        return (
            f"Your current path starts with: {preview}. Ask about next steps, skill gaps, "
            f"or why a course was recommended."
        )
    return (
        "Ask about next steps, skill gaps, weekly hours, or why a recommendation was made. "
        "Generate a path to get more specific answers."
    )
