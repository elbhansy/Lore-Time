import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.factions.faction_intelligence import FactionIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetFactionLeadershipUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, faction_id: str, chapter: int
    ) -> list[dict[str, Any]]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        fac_meta = entities.factions.get(faction_id)
        if (
            not fac_meta
            or not fac_meta.introduced_chapter
            or fac_meta.introduced_chapter > chapter
        ):
            raise ValueError("Faction not found.")

        history = FactionIntelligence.get_leadership_history(ws, faction_id)

        results = []
        for ls in history:
            char_meta = entities.characters.get(ls.leader_id)
            char_name = char_meta.name if char_meta else ls.leader_id
            results.append(
                {
                    "leader_id": ls.leader_id,
                    "leader_name": char_name,
                    "active": ls.active,
                    "started_at": ls.started_at,
                    "ended_at": ls.ended_at,
                }
            )

        return results
