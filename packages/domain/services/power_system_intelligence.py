from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.state.world_state import WorldState


class PowerSystemIntelligence:
    @staticmethod
    def get_characters_at_rank(
        state: WorldState, power_system_id: str, rank_id: str, reader_chapter: int
    ) -> list[str]:
        characters = []
        for char_id, char_state in state.characters.items():
            if not char_state.exists or not char_state.alive:
                continue

            current_rank = PowerProgressionService.get_current_rank(
                state, char_id, power_system_id, reader_chapter
            )
            if current_rank == rank_id:
                characters.append(char_id)

        return characters

    @staticmethod
    def get_rank_population(
        state: WorldState, power_system_id: str, reader_chapter: int
    ) -> dict[str, int]:
        distribution = {}
        for char_id, char_state in state.characters.items():
            if not char_state.exists or not char_state.alive:
                continue

            current_rank = PowerProgressionService.get_current_rank(
                state, char_id, power_system_id, reader_chapter
            )
            if current_rank:
                distribution[current_rank] = distribution.get(current_rank, 0) + 1

        return distribution
