from dataclasses import dataclass


@dataclass
class SkillState:
    character_id: str
    skill_id: str
    active: bool
    unlocked_at: int
    upgraded_at: int | None = None
    lost_at: int | None = None
