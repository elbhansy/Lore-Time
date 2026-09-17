from packages.domain.comparison.character_diff import ChangeType, CharacterDiff
from packages.domain.comparison.power_diff import PowerDiff
from packages.domain.comparison.relationship_diff import (
    RelationshipChangeType,
    RelationshipDiff,
)
from packages.domain.comparison.skill_diff import SkillDiff
from packages.domain.comparison.temporal_comparison import TemporalComparison
from packages.domain.state.world_state import WorldState


class WorldStateComparator:
    @staticmethod
    def compare(state_a: WorldState, state_b: WorldState) -> TemporalComparison:
        character_changes = []
        power_changes = []
        skill_changes = []
        relationship_changes = []

        # 1. Characters
        all_char_ids = sorted(
            list(set(state_a.characters.keys()) | set(state_b.characters.keys()))
        )

        for cid in all_char_ids:
            char_a = state_a.characters.get(cid)
            char_b = state_b.characters.get(cid)

            exists_a = char_a is not None and char_a.exists
            exists_b = char_b is not None and char_b.exists

            if not exists_a and exists_b:
                character_changes.append(
                    CharacterDiff(
                        character_id=cid,
                        change_type=ChangeType.INTRODUCED,
                        before_status=None,
                        after_status="alive" if char_b.alive else "dead",
                    )
                )
            elif exists_a and not exists_b:
                character_changes.append(
                    CharacterDiff(
                        character_id=cid,
                        change_type=ChangeType.REMOVED,
                        before_status="alive" if char_a.alive else "dead",
                        after_status=None,
                    )
                )
            elif exists_a and exists_b:
                # Check for death/resurrection
                if char_a.alive != char_b.alive:
                    character_changes.append(
                        CharacterDiff(
                            character_id=cid,
                            change_type=ChangeType.CHANGED,
                            before_status="alive" if char_a.alive else "dead",
                            after_status="alive" if char_b.alive else "dead",
                        )
                    )

                # Power Check
                if char_a.rank != char_b.rank:
                    power_changes.append(
                        PowerDiff(
                            character_id=cid,
                            before_rank=char_a.rank,
                            after_rank=char_b.rank,
                        )
                    )

                # Skills Check
                new_skills = sorted(
                    list(char_b.unlocked_skills - char_a.unlocked_skills)
                )
                if new_skills:
                    skill_changes.append(
                        SkillDiff(character_id=cid, unlocked_skills=new_skills)
                    )

        # 2. Relationships
        all_rel_keys = sorted(
            list(set(state_a.relationships.keys()) | set(state_b.relationships.keys()))
        )

        for key in all_rel_keys:
            rel_a = state_a.relationships.get(key)
            rel_b = state_b.relationships.get(key)

            active_a = rel_a is not None and rel_a.active
            active_b = rel_b is not None and rel_b.active

            source_id, target_id = key

            if not active_a and active_b:
                relationship_changes.append(
                    RelationshipDiff(
                        source_id=source_id,
                        target_id=target_id,
                        change_type=RelationshipChangeType.CREATED,
                        before_type=None,
                        after_type=rel_b.relationship_type.value,
                    )
                )
            elif active_a and not active_b:
                relationship_changes.append(
                    RelationshipDiff(
                        source_id=source_id,
                        target_id=target_id,
                        change_type=RelationshipChangeType.ENDED,
                        before_type=rel_a.relationship_type.value,
                        after_type=None,
                    )
                )
            elif active_a and active_b:
                if rel_a.relationship_type != rel_b.relationship_type:
                    relationship_changes.append(
                        RelationshipDiff(
                            source_id=source_id,
                            target_id=target_id,
                            change_type=RelationshipChangeType.CHANGED,
                            before_type=rel_a.relationship_type.value,
                            after_type=rel_b.relationship_type.value,
                        )
                    )

        return TemporalComparison(
            from_chapter=state_a.chapter.value,
            to_chapter=state_b.chapter.value,
            character_changes=character_changes,
            power_changes=power_changes,
            relationship_changes=relationship_changes,
            skill_changes=skill_changes,
        )
