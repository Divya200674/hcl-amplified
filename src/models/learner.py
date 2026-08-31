from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningGoal(BaseModel):
    title: str
    description: str = ""
    target_domain: str = ""
    deadline_weeks: Optional[int] = None


class LearnerProfile(BaseModel):
    user_id: str = "default_user"
    name: str = "Learner"
    interests: list[str] = Field(default_factory=list)
    skill_level: SkillLevel = SkillLevel.BEGINNER
    completed_items: list[str] = Field(default_factory=list)
    current_skills: list[str] = Field(default_factory=list)
    goals: list[LearningGoal] = Field(default_factory=list)
    preferred_style: str = "hands-on"
    weekly_hours: int = 10
    feedback_scores: dict[str, int] = Field(default_factory=dict)

    def to_context_text(self) -> str:
        goals_text = ", ".join(g.title for g in self.goals) or "Not specified"
        return (
            f"Name: {self.name}\n"
            f"Skill level: {self.skill_level.value}\n"
            f"Interests: {', '.join(self.interests) or 'None'}\n"
            f"Current skills: {', '.join(self.current_skills) or 'None'}\n"
            f"Completed: {', '.join(self.completed_items) or 'None'}\n"
            f"Goals: {goals_text}\n"
            f"Preferred style: {self.preferred_style}\n"
            f"Weekly hours: {self.weekly_hours}"
        )
