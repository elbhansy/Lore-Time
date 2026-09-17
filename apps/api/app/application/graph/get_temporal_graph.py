import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.graph.graph_entities import EntityMetadata, GraphEntities
from packages.domain.graph.temporal_graph import TemporalGraph
from packages.domain.services.temporal_graph_builder import TemporalGraphBuilder
from packages.domain.value_objects.entity_id import EntityId


class GraphEntitiesProvider:
    """
    In a real app, this would query repositories to build the GraphEntities container.
    For this prototype, we'll mock or load static JSON.
    """

    def get_static_entities(self, series_id: EntityId) -> GraphEntities:
        # Mocking for M1.4. In a real system, we fetch characters, factions, systems, ranks, skills from DB
        # This static data is assumed to be the "truth" dictionary, which the Builder filters by readerChapter.
        return GraphEntities(
            characters={},
            factions={
                "f1": EntityMetadata(name="Radiant Church", introduced_chapter=1),
                "f2": EntityMetadata(name="Shadow Hand", introduced_chapter=10),
            },
            power_systems={"ps1": EntityMetadata(name="Aura Cultivation")},
            ranks={
                "rank_a": EntityMetadata(
                    name="Aura Master", introduced_chapter=5, system_id="ps1"
                ),
                "rank_s": EntityMetadata(
                    name="Aura Grandmaster", introduced_chapter=50, system_id="ps1"
                ),
            },
            skills={
                "skill_1": EntityMetadata(name="Aura Blade"),
                "skill_2": EntityMetadata(name="Aura Shield"),
            },
        )


class GetTemporalGraphUseCase:
    def __init__(
        self,
        get_world_state_uc: GetWorldStateUseCase,
        entities_provider: GraphEntitiesProvider,
    ):
        self.get_world_state_uc = get_world_state_uc
        self.entities_provider = entities_provider

    def execute(self, series_id: uuid.UUID, chapter: int) -> TemporalGraph:
        series_eid = EntityId(series_id)

        # 1. Get temporal WorldState
        world_state = self.get_world_state_uc.execute(series_id, chapter)

        # 2. Get static entity reference data
        entities = self.entities_provider.get_static_entities(series_eid)

        # 3. Project to Graph safely via Domain Builder
        graph = TemporalGraphBuilder.build(world_state, entities)

        return graph
