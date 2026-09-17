import uuid

from packages.domain.entities.rank import Rank
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.rank_repository import RankRepository
from packages.domain.services.event_ordering import sort_events
from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import InvalidChapter


class GetRankProgressionUseCase:
    def __init__(self, event_repo: EventRepository, rank_repo: RankRepository):
        self.event_repo = event_repo
        self.rank_repo = rank_repo

    def execute(
        self, series_id: uuid.UUID, character_id: uuid.UUID, reader_chapter: int
    ) -> list[Rank]:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter must be positive")

        series_entity_id = EntityId(series_id)
        char_entity_id = EntityId(character_id)

        # Get all events
        envelopes = self.event_repo.get_all_by_series(series_entity_id)

        # Ensure chronological order
        envelopes = sort_events(envelopes)

        # Apply PowerProgressionService to get rank history
        rank_ids = PowerProgressionService.get_rank_history(
            character_id=char_entity_id,
            envelopes=envelopes,
            reader_chapter=reader_chapter,
        )

        # Hydrate rank IDs into full Rank entities
        # We must manually fetch them, or rely on a generic RankRepository method.
        # This is where a batch get or caching is useful. We will just fetch individually for M0.9.
        ranks = []
        for r_id in rank_ids:
            rank = self.rank_repo.get(r_id)
            # Second layer of defense: Verify the rank metadata itself isn't a spoiler
            # Although the event chapter should guarantee it's safe, we double check.
            if rank and rank.introduced_chapter.value <= reader_chapter:
                ranks.append(rank)

        return ranks
