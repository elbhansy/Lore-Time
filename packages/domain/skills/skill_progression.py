from typing import Any

from packages.domain.skills.skill_intelligence import SkillIntelligence
from packages.domain.skills.skill_relation import SkillRelation, SkillRelationScope
from packages.domain.state.world_state import WorldState


class SkillProgressionService:
    """
    Reconstructs the evolution/upgrade path of a skill for a character,
    respecting what is visible at reader_chapter.
    """

    @staticmethod
    def get_progression(
        state: WorldState,
        character_id: str,
        reader_chapter: int,
        static_relations: list[SkillRelation],
    ) -> dict[str, Any]:
        """
        Builds a tree/path of the character's active skills.
        In a real application this would build a proper graph or hierarchical dict.
        For this prototype, we return a list of active skills and the relations that apply to them.
        """
        active_skills = SkillIntelligence.get_active_skills(state, character_id)
        visible_relations = SkillIntelligence.get_visible_relations(
            state, reader_chapter, static_relations
        )

        # Filter relations that apply to this character (Universal OR specific to them)
        applicable_relations = []
        for rel in visible_relations:
            if rel.scope == SkillRelationScope.UNIVERSAL:
                applicable_relations.append(rel)
            elif (
                rel.scope == SkillRelationScope.CHARACTER_SPECIFIC
                and rel.character_id == character_id
            ):
                applicable_relations.append(rel)

        # Return a projection that the UI can render
        return {
            "active_skills": [s.__dict__ for s in active_skills],
            "relations": [r.__dict__ for r in applicable_relations],
        }
