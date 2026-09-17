import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.comparison.temporal_comparison import TemporalComparison
from packages.domain.comparison.world_state_comparator import WorldStateComparator

from ..exceptions import InvalidChapter


class CompareWorldStatesUseCase:
    def __init__(self, get_world_state_uc: GetWorldStateUseCase):
        self.get_world_state_uc = get_world_state_uc

    def execute(
        self,
        series_id: uuid.UUID,
        from_chapter: int,
        to_chapter: int,
        reader_chapter: int,
    ) -> TemporalComparison:
        # Spoiler Firewall & Input Validation
        if from_chapter < 1:
            raise InvalidChapter("from_chapter must be positive")
        if from_chapter >= to_chapter:
            raise InvalidChapter("from_chapter must be strictly less than to_chapter")
        if to_chapter > reader_chapter:
            raise InvalidChapter(
                f"to_chapter ({to_chapter}) cannot exceed reader_chapter ({reader_chapter})"
            )

        # Reconstruct States
        state_from = self.get_world_state_uc.execute(series_id, from_chapter)
        state_to = self.get_world_state_uc.execute(series_id, to_chapter)

        # Compare
        comparison = WorldStateComparator.compare(state_from, state_to)
        return comparison
