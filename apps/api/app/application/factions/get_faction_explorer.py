import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.factions.faction_intelligence import FactionIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetFactionExplorerUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(self, series_id: uuid.UUID, chapter: int) -> list[dict[str, Any]]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        results = []
        for fac_id, meta in entities.factions.items():
            if meta.introduced_chapter and meta.introduced_chapter <= chapter:
                # Get basic stats to show in explorer list
                mem_count = len(FactionIntelligence.get_active_members(ws, fac_id))
                results.append(
                    {
                        "id": fac_id,
                        "name": meta.name,
                        "member_count": mem_count,
                        "introduced_chapter": meta.introduced_chapter,
                    }
                )

        # Sort alphabetically
        results.sort(key=lambda x: x["name"])
        return results
