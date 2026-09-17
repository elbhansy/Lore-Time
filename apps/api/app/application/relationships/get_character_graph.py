import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.schemas.relationship import (
    CharacterGraphResponse,
    CharacterNode,
    RelationshipEdge,
)
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import CharacterNotFound, InvalidChapter


class GetCharacterGraphUseCase:
    def __init__(
        self,
        character_repo: CharacterRepository,
        get_world_state_uc: GetWorldStateUseCase,
    ):
        self.character_repo = character_repo
        self.get_world_state_uc = get_world_state_uc

    def execute(
        self,
        series_id: uuid.UUID,
        character_id: uuid.UUID,
        reader_chapter: int,
        depth: int,
    ) -> CharacterGraphResponse:
        if depth not in (1, 2):
            raise ValueError("Depth must be 1 or 2")

        if reader_chapter < 1:
            raise InvalidChapter("Chapter must be positive")

        # 1. Reconstruct WorldState @ reader_chapter
        world_state = self.get_world_state_uc.execute(series_id, reader_chapter)

        # 2. Validate Root Character
        char_id_str = str(character_id)
        if (
            char_id_str not in world_state.characters
            or not world_state.characters[char_id_str].exists
        ):
            raise CharacterNotFound(
                f"Character {character_id} not available at chapter {reader_chapter}"
            )

        # 3. BFS Traversal
        visited_nodes = {char_id_str}
        edges_list = []

        current_level = {char_id_str}

        for current_depth in range(depth):
            next_level = set()

            for key, rel in world_state.relationships.items():
                if not rel.active:
                    continue

                source_id, target_id = key

                # Check if this edge connects to our current level
                if source_id in current_level or target_id in current_level:
                    # We add the edge if we haven't processed it yet.
                    # We track edges inherently by creating a unique ID
                    edge_id = f"{source_id}-{target_id}"

                    # Prevent duplicates if graph has cycles
                    if not any(e.id == edge_id for e in edges_list):
                        edges_list.append(
                            RelationshipEdge(
                                id=edge_id,
                                source=source_id,
                                target=target_id,
                                type=rel.relationship_type.value,
                                active=rel.active,
                            )
                        )

                    next_level.add(source_id)
                    next_level.add(target_id)
                    visited_nodes.add(source_id)
                    visited_nodes.add(target_id)

            current_level = next_level

        # 4. Resolve Nodes (Enforce WorldState availability)
        nodes_list = []
        for c_id in visited_nodes:
            # Spoiler Firewall check for 1-hop and 2-hop nodes
            char_state = world_state.characters.get(c_id)
            if not char_state or not char_state.exists:
                continue

            char_entity = self.character_repo.get(EntityId(c_id))
            name = char_entity.name if char_entity else "Unknown Character"

            nodes_list.append(
                CharacterNode(
                    id=c_id, name=name, rank=char_state.rank, alive=char_state.alive
                )
            )

        # 5. Deterministic Sort
        nodes_list.sort(key=lambda x: x.id)
        edges_list.sort(key=lambda x: x.id)

        return CharacterGraphResponse(
            root_character_id=char_id_str,
            chapter=reader_chapter,
            depth=depth,
            nodes=nodes_list,
            edges=edges_list,
        )
