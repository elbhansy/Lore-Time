from packages.domain.power.power_progression import PowerProgression
from packages.domain.power.rank_transition import RankTransition
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.entity_id import EntityId


class PowerProgressionService:
    @staticmethod
    def get_progression(
        state: WorldState, character_id: str, power_system_id: str, reader_chapter: int
    ) -> PowerProgression:
        key = (character_id, power_system_id)
        transitions = state.rank_transitions.get(key, [])

        valid_transitions = []
        current_rank = None

        for t in transitions:
            if t.chapter <= reader_chapter:
                valid_transitions.append(t)
                current_rank = t.to_rank_id

        return PowerProgression(
            character_id=character_id,
            power_system_id=power_system_id,
            current_rank=current_rank,
            transitions=valid_transitions,
        )

    @staticmethod
    def get_current_rank(
        state: WorldState, character_id: str, power_system_id: str, reader_chapter: int
    ) -> str | None:
        progression = PowerProgressionService.get_progression(
            state, character_id, power_system_id, reader_chapter
        )
        return progression.current_rank

    @staticmethod
    def get_rank_at(
        state: WorldState, character_id: str, power_system_id: str, chapter: int
    ) -> str | None:
        # Using get_progression with the target chapter effectively does this
        progression = PowerProgressionService.get_progression(
            state, character_id, power_system_id, chapter
        )
        return progression.current_rank

    @staticmethod
    def get_history(
        state: WorldState, character_id: str, power_system_id: str, reader_chapter: int
    ) -> list[RankTransition]:
        progression = PowerProgressionService.get_progression(
            state, character_id, power_system_id, reader_chapter
        )
        return progression.transitions

    @staticmethod
    def get_rank_history(
        character_id: EntityId | str, envelopes: list[object], reader_chapter: int
    ) -> list[EntityId]:
        char_id_str = str(character_id)
        rank_history: list[EntityId] = []
        for env in envelopes:
            event = getattr(env, "event", env)
            ch_num = getattr(env, "chapter_number", None)
            chapter_val = (
                ch_num.value
                if ch_num is not None and hasattr(ch_num, "value")
                else getattr(event, "metadata", {}).get("chapter_number", 0)
            )
            if chapter_val > reader_chapter:
                continue

            event_type = getattr(event, "type", None)
            event_type_val = (
                event_type.value if hasattr(event_type, "value") else str(event_type)
            )
            if event_type_val == "POWER_RANK_CHANGED":
                sub_id = getattr(event, "subject_id", None)
                if str(sub_id) == char_id_str:
                    new_state = getattr(event, "new_state", {})
                    rank_id = new_state.get("rank_id") or new_state.get("to_rank")
                    if rank_id:
                        rank_history.append(EntityId(rank_id))
        return rank_history
