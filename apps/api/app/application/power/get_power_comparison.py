import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.services.power_progression import PowerProgressionService
from packages.domain.services.rank_comparison import RankComparisonService
from packages.domain.value_objects.entity_id import EntityId


class GetPowerComparisonUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self,
        series_id: uuid.UUID,
        character_a: str,
        character_b: str,
        power_system_id: str,
        chapter: int,
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        rank_a_id = PowerProgressionService.get_current_rank(
            ws, character_a, power_system_id, chapter
        )
        rank_b_id = PowerProgressionService.get_current_rank(
            ws, character_b, power_system_id, chapter
        )

        rank_a_meta = entities.ranks.get(rank_a_id) if rank_a_id else None
        rank_b_meta = entities.ranks.get(rank_b_id) if rank_b_id else None

        if not rank_a_meta or not rank_b_meta:
            return {
                "character_a": {"rank": None, "order": None},
                "character_b": {"rank": None, "order": None},
                "result": "NOT_COMPARABLE",
            }

        result = RankComparisonService.compare(
            character_a,
            rank_a_meta.power_system_id,
            rank_a_id,
            rank_a_meta.order,
            character_b,
            rank_b_meta.power_system_id,
            rank_b_id,
            rank_b_meta.order,
        )

        return {
            "character_a": {"rank": rank_a_meta.name, "order": rank_a_meta.order},
            "character_b": {"rank": rank_b_meta.name, "order": rank_b_meta.order},
            "result": result,
        }
