import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.skills.skill_intelligence import SkillIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetSkillExplorerUseCase:
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
        for skill_id, meta in entities.skills.items():
            # Check spoiler firewall
            if meta.introduced_chapter and meta.introduced_chapter <= chapter:
                users = SkillIntelligence.get_skill_users(ws, skill_id)
                results.append(
                    {
                        "id": skill_id,
                        "name": meta.name,
                        "introduced_chapter": meta.introduced_chapter,
                        "active_users_count": len(users),
                    }
                )

        results.sort(key=lambda x: x["name"])
        return results
