from dataclasses import dataclass


@dataclass(frozen=True)
class SkillDiff:
    character_id: str
    unlocked_skills: list[str]
