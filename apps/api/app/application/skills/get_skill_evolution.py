import uuid
from typing import Any

from apps.api.app.application.graph.get_temporal_graph import GraphEntitiesProvider
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.skills.skill_intelligence import SkillIntelligence
from packages.domain.value_objects.entity_id import EntityId


class GetSkillEvolutionUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(
        self, series_id: uuid.UUID, skill_id: str, chapter: int
    ) -> dict[str, Any]:
        ws = self.get_world_state_uc.execute(series_id, chapter)
        entities = self.entities_provider.get_static_entities(EntityId(series_id))

        # Check spoiler firewall
        meta = entities.skills.get(skill_id)
        if not meta or (meta.introduced_chapter and meta.introduced_chapter > chapter):
            raise ValueError("Skill not found or not yet introduced.")

        static_relations = (
            entities.skill_relations if hasattr(entities, "skill_relations") else []
        )
        visible_relations = SkillIntelligence.get_visible_relations(
            ws, chapter, static_relations
        )

        # Build evolution tree nodes and edges relative to this skill
        nodes = {skill_id: meta}
        edges = []

        # BFS or simply iterative collection to find all related skills in the tree
        # For prototype, we'll just gather all visible relations and filter to connected components
        # A full implementation would do a graph traversal.
        for rel in visible_relations:
            if rel.source_skill_id == skill_id or rel.target_skill_id == skill_id:
                edges.append(rel)
                if (
                    rel.source_skill_id not in nodes
                    and rel.source_skill_id in entities.skills
                ):
                    nodes[rel.source_skill_id] = entities.skills[rel.source_skill_id]
                if (
                    rel.target_skill_id not in nodes
                    and rel.target_skill_id in entities.skills
                ):
                    nodes[rel.target_skill_id] = entities.skills[rel.target_skill_id]

        return {
            "skill_id": skill_id,
            "nodes": [{"id": k, "name": v.name} for k, v in nodes.items()],
            "edges": [
                {
                    "id": e.id,
                    "source": e.source_skill_id,
                    "target": e.target_skill_id,
                    "type": e.type,
                }
                for e in edges
            ],
        }
