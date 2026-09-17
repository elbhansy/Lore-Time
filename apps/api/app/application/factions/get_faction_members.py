import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.factions.faction_intelligence import FactionIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetFactionMembersUseCase:
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

        # Check spoiler firewall implicitly via builder, but since we are bypassing graph builder here, we check manually
        fac_meta = entities.factions.get(faction_id)
        if (
            not fac_meta
            or not fac_meta.introduced_chapter
            or fac_meta.introduced_chapter > chapter
        ):
            raise ValueError("Faction not found.")

        history = FactionIntelligence.get_membership_history(ws, faction_id)

        results = []
        for ms in history:
            char_meta = entities.characters.get(ms.character_id)
            char_name = char_meta.name if char_meta else ms.character_id
            results.append(
                {
                    "character_id": ms.character_id,
                    "character_name": char_name,
                    "active": ms.active,
                    "joined_at": ms.joined_at,
                    "left_at": ms.left_at,
                }
            )

        return results
