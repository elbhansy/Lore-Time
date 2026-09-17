import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.skills.skill_progression import SkillProgressionService
from packages.domain.value_objects.entity_id import EntityId


class GetCharacterSkillsUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, character_id: str, chapter: int
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        # We need static_relations
        # For prototype, we'll just pull them from entities, assuming GraphEntitiesProvider fetches them
        static_relations = (
            entities.skill_relations if hasattr(entities, "skill_relations") else []
        )

        progression = SkillProgressionService.get_progression(
            ws, character_id, chapter, static_relations
        )

        # Map skill IDs to names
        for s in progression["active_skills"]:
            meta = entities.skills.get(s["skill_id"])
            s["skill_name"] = meta.name if meta else s["skill_id"]

        return progression
