import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.factions.faction_intelligence import FactionIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetFactionProfileUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, faction_id: str, chapter: int
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)

        # 1. Spoiler Firewall: Check if faction is introduced
        entities = self.entities_provider.get_static_entities(EntityId(series_id))
        fac_meta = entities.factions.get(faction_id)
        if (
            not fac_meta
            or not fac_meta.introduced_chapter
            or fac_meta.introduced_chapter > chapter
        ):
            raise ValueError("Faction not found or not yet introduced.")

        # 2. Extract Data using FactionIntelligence
        active_members = FactionIntelligence.get_active_members(ws, faction_id)
        current_leader = FactionIntelligence.get_current_leader(ws, faction_id)
        relationships = FactionIntelligence.get_faction_relationships(ws, faction_id)

        # Map leader name
        leader_name = None
        if current_leader:
            leader_meta = entities.characters.get(current_leader)
            leader_name = leader_meta.name if leader_meta else current_leader

        return {
            "id": faction_id,
            "name": fac_meta.name,
            "description": fac_meta.description,
            "introduced_chapter": fac_meta.introduced_chapter,
            "member_count": len(active_members),
            "leader_id": current_leader,
            "leader_name": leader_name,
            "active_relationships_count": len(relationships),
        }
