from enum import Enum

from pydantic import BaseModel, Field


class ItemType(str, Enum):
    COURSE = "course"
    PROJECT = "project"
    ASSESSMENT = "assessment"


class LearningItem(BaseModel):
    id: str
    title: str
    domain: str
    level: str
    duration_weeks: float
    skills_taught: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    description: str = ""
    item_type: ItemType = ItemType.COURSE
    popularity: float = 0.5

    def searchable_text(self) -> str:
        return " ".join(
            [
                self.title,
                self.domain,
                self.description,
                " ".join(self.skills_taught),
                self.item_type.value,
            ]
        )
