import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.schemas.relationship import (
    CharacterNode,
    RelationshipEdge,
    RelationshipGraphResponse,
)
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.value_objects.entity_id import EntityId


class GetRelationshipGraphUseCase:
    def __init__(
        self,
        character_repo: CharacterRepository,
        get_world_state_uc: GetWorldStateUseCase,
    ):
        self.character_repo = character_repo
        self.get_world_state_uc = get_world_state_uc

    def execute(
        self, series_id: uuid.UUID, reader_chapter: int, rel_type: str | None = None
    ) -> RelationshipGraphResponse:
        # 1. Reconstruct WorldState @ reader_chapter
        world_state = self.get_world_state_uc.execute(series_id, reader_chapter)

        # 2. Extract active relationships and apply filter
        edges = []
        character_ids = set()

        for key, rel in world_state.relationships.items():
            if not rel.active:
                continue

            if (
                rel_type
                and rel_type != "ALL"
                and rel.relationship_type.value != rel_type
            ):
                continue

            source_id = rel.subject_id.value
            target_id = rel.target_id.value

            # The edge ID is the identity of the relationship tuple
            edge_id = f"{source_id}-{target_id}"

            edges.append(
                RelationshipEdge(
                    id=edge_id,
                    source=source_id,
                    target=target_id,
                    type=rel.relationship_type.value,
                    active=rel.active,
                )
            )

            character_ids.add(source_id)
            character_ids.add(target_id)

        # 3. Create nodes for all characters involved
        nodes = []
        for char_id in character_ids:
            # Check if character is introduced in WorldState
            char_state = world_state.characters.get(char_id)
            if not char_state or not char_state.exists:
                continue

            # Fetch character metadata
            char_entity = self.character_repo.get(EntityId(char_id))
            name = char_entity.name if char_entity else "Unknown Character"

            nodes.append(
                CharacterNode(
                    id=char_id, name=name, rank=char_state.rank, alive=char_state.alive
                )
            )

        return RelationshipGraphResponse(nodes=nodes, edges=edges)
