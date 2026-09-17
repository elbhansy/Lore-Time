import uuid

from packages.domain.entities.rank import Rank
from packages.domain.repositories.power_system_repository import PowerSystemRepository
from packages.domain.repositories.rank_repository import RankRepository
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import InvalidChapter


class GetRanksUseCase:
    def __init__(
        self, rank_repo: RankRepository, power_system_repo: PowerSystemRepository
    ):
        self.rank_repo = rank_repo
        self.power_system_repo = power_system_repo

    def execute(
        self, series_id: uuid.UUID, power_system_id: uuid.UUID, reader_chapter: int
    ) -> list[Rank]:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter must be positive")

        ps_id = EntityId(power_system_id)
        ps = self.power_system_repo.get(ps_id)

        # Verify system exists and belongs to the series
        if not ps or ps.series_id.value != series_id:
            raise ValueError(
                f"Power System {power_system_id} not found in series {series_id}"
            )

        # Spoiler Firewall: Only return ranks introduced up to reader_chapter
        return self.rank_repo.get_visible_ranks(ps_id, reader_chapter)
