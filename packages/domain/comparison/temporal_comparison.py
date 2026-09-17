from dataclasses import dataclass

from .character_diff import CharacterDiff
from .power_diff import PowerDiff
from .relationship_diff import RelationshipDiff
from .skill_diff import SkillDiff


@dataclass(frozen=True)
class TemporalComparison:
    from_chapter: int
    to_chapter: int
    character_changes: list[CharacterDiff]
    power_changes: list[PowerDiff]
    relationship_changes: list[RelationshipDiff]
    skill_changes: list[SkillDiff]

    @property
    def summary(self) -> dict:
        chars_introduced = sum(
            1 for c in self.character_changes if c.change_type.value == "INTRODUCED"
        )
        chars_removed = sum(
            1 for c in self.character_changes if c.change_type.value == "REMOVED"
        )

        return {
            "characters_introduced": chars_introduced,
            "characters_removed": chars_removed,
            "power_changes": len(self.power_changes),
            "skills_unlocked": sum(len(s.unlocked_skills) for s in self.skill_changes),
            "relationships_changed": len(self.relationship_changes),
        }
