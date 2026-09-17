from packages.domain.skills.skill_relation import SkillRelation
from packages.domain.skills.skill_state import SkillState
from packages.domain.state.world_state import WorldState


class SkillIntelligence:
    @staticmethod
    def get_active_skills(state: WorldState, character_id: str) -> list[SkillState]:
        active_skills = []
        for (char_id, skill_id), history in state.skills.items():
            if char_id == character_id:
                for s in history:
                    if s.active:
                        active_skills.append(s)
        return active_skills

    @staticmethod
    def get_skill_history(
        state: WorldState, character_id: str, skill_id: str
    ) -> list[SkillState]:
        key = (character_id, skill_id)
        if key in state.skills:
            return list(state.skills[key])
        return []

    @staticmethod
    def get_skill_users(state: WorldState, skill_id: str) -> list[str]:
        users = []
        for (char_id, s_id), history in state.skills.items():
            if s_id == skill_id:
                for s in history:
                    if s.active:
                        users.append(char_id)
                        break
        return users

    @staticmethod
    def get_visible_relations(
        state: WorldState, reader_chapter: int, static_relations: list[SkillRelation]
    ) -> list[SkillRelation]:
        """
        Merge static relations (filtered by introduced_chapter) with dynamic relations revealed by events up to reader_chapter.
        """
        visible = []

        # 1. Static rules
        for rel in static_relations:
            if rel.introduced_chapter and rel.introduced_chapter <= reader_chapter:
                visible.append(rel)

        # 2. Dynamic event-revealed rules (from WorldState)
        for rel_id, rel in state.skill_relations.items():
            if rel.introduced_chapter and rel.introduced_chapter <= reader_chapter:
                # We avoid duplicates if the event just reinforces a static rule
                if not any(r.id == rel.id for r in visible):
                    visible.append(rel)

        return visible
