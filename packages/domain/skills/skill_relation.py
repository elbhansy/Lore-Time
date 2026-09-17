from dataclasses import dataclass
from enum import Enum


class SkillRelationType(str, Enum):
    UPGRADED_FROM = "UPGRADED_FROM"
    EVOLVED_FROM = "EVOLVED_FROM"
    REPLACED_BY = "REPLACED_BY"
    COMBINES_WITH = "COMBINES_WITH"
    REQUIRES = "REQUIRES"


class SkillRelationScope(str, Enum):
    UNIVERSAL = "UNIVERSAL"
    CHARACTER_SPECIFIC = "CHARACTER_SPECIFIC"


@dataclass
class SkillRelation:
    id: str
    source_skill_id: str
    target_skill_id: str
    type: SkillRelationType
    scope: SkillRelationScope
    character_id: str | None = None
    introduced_chapter: int | None = None
