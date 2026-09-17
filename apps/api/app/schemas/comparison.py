from pydantic import BaseModel


class CharacterDiffDTO(BaseModel):
    character_id: str
    change_type: str
    before_status: str | None = None
    after_status: str | None = None


class PowerDiffDTO(BaseModel):
    character_id: str
    before_rank: str | None = None
    after_rank: str | None = None


class RelationshipDiffDTO(BaseModel):
    source_id: str
    target_id: str
    change_type: str
    before_type: str | None = None
    after_type: str | None = None


class SkillDiffDTO(BaseModel):
    character_id: str
    unlocked_skills: list[str]


class TemporalComparisonResponse(BaseModel):
    from_chapter: int
    to_chapter: int
    summary: dict[str, int]
    character_changes: list[CharacterDiffDTO]
    power_changes: list[PowerDiffDTO]
    relationship_changes: list[RelationshipDiffDTO]
    skill_changes: list[SkillDiffDTO]
