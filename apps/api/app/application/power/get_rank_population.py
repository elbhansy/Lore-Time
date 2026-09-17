import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.services.power_system_intelligence import PowerSystemIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetRankPopulationUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, power_system_id: str, rank_id: str, chapter: int
    ) -> list[str]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        # Firewall
        rank_meta = entities.ranks.get(rank_id)
        if not rank_meta or (
            rank_meta.introduced_chapter and rank_meta.introduced_chapter > chapter
        ):
            return []

        return PowerSystemIntelligence.get_characters_at_rank(
            ws, power_system_id, rank_id, chapter
        )


class GetRankDistributionUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, power_system_id: str, chapter: int
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        population = PowerSystemIntelligence.get_rank_population(
            ws, power_system_id, chapter
        )

        distribution = []
        # Filter ranks by readerChapter
        valid_ranks = [
            r
            for r in entities.ranks.values()
            if r.power_system_id == power_system_id
            and (not r.introduced_chapter or r.introduced_chapter <= chapter)
        ]

        for rank in valid_ranks:
            distribution.append(
                {
                    "rank_id": rank.id,
                    "rank_name": rank.name,
                    "order": rank.order,
                    "count": population.get(rank.id, 0),
                }
            )

        distribution.sort(key=lambda x: x["order"])

        return {"power_system_id": power_system_id, "distribution": distribution}
