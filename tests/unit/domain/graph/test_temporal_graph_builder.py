from packages.domain.graph.edge_type import EdgeType
from packages.domain.graph.graph_entities import EntityMetadata, GraphEntities
from packages.domain.services.temporal_graph_builder import TemporalGraphBuilder
from packages.domain.state.character_state import CharacterState
from packages.domain.state.relationship_state import RelationshipState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.relationship_type import RelationshipType


def get_static_entities():
    return GraphEntities(
        characters={
            "c1": EntityMetadata("Hero"),
            "c2": EntityMetadata("Villain"),
            "c3": EntityMetadata("Future Guy"),  # Introduced chapter 200
        },
        factions={
            "f1": EntityMetadata("Good Guys", introduced_chapter=10),
            "f2": EntityMetadata("Future Faction", introduced_chapter=200),
        },
        power_systems={"ps1": EntityMetadata("Magic")},
        ranks={
            "r1": EntityMetadata("Novice", introduced_chapter=5, system_id="ps1"),
            "r2": EntityMetadata("God", introduced_chapter=200, system_id="ps1"),
        },
        skills={"s1": EntityMetadata("Fireball")},
    )


def test_graph_builder_determinism_and_spoiler_firewall():
    # WorldState at Chapter 100
    ws = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    ws.characters["c1"] = CharacterState(
        EntityId("c1"), exists=True, faction_id="f1", rank="r1", unlocked_skills={"s1"}
    )
    ws.characters["c2"] = CharacterState(
        EntityId("c2"), exists=True, faction_id="f2", rank="r2"
    )  # Has future rank and faction!
    ws.relationships[("c1", "c2")] = RelationshipState(
        EntityId("c1"),
        EntityId("c2"),
        RelationshipType.ENEMY,
        active=True,
        started_at=50,
    )

    entities = get_static_entities()
    graph = TemporalGraphBuilder.build(ws, entities)

    # 1. Determinism
    assert len(graph.nodes) > 0

    node_ids = [n.id for n in graph.nodes]

    # 2. Future Character (c3) not in graph because not in WorldState exists=True
    assert "c3" not in node_ids

    # 3. Faction projection (c1 -> f1 is allowed, f1 introduced <= 100)
    assert "f1" in node_ids
    assert any(
        e.source_id == "c1" and e.target_id == "f1" and e.type == EdgeType.MEMBER_OF
        for e in graph.edges
    )

    # 4. Future Faction Firewall (c2 is in f2, but f2 introduced at 200 > 100)
    assert "f2" not in node_ids
    assert not any(e.target_id == "f2" for e in graph.edges)

    # 5. Future Rank Firewall (c2 is rank r2, but r2 introduced at 200 > 100)
    assert "r2" not in node_ids
    assert not any(e.target_id == "r2" for e in graph.edges)

    # 6. Valid Rank projection
    assert "r1" in node_ids
    assert any(
        e.source_id == "c1" and e.target_id == "r1" and e.type == EdgeType.HAS_RANK
        for e in graph.edges
    )

    # 7. Valid Skill projection
    assert "s1" in node_ids
    assert any(
        e.source_id == "c1"
        and e.target_id == "s1"
        and e.type == EdgeType.UNLOCKED_SKILL
        for e in graph.edges
    )

    # 8. Relationship projection
    assert any(
        e.source_id == "c1" and e.target_id == "c2" and e.type == EdgeType.ENEMY
        for e in graph.edges
    )


def test_ended_relationship_not_projected():
    ws = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    ws.characters["c1"] = CharacterState(EntityId("c1"), exists=True)
    ws.characters["c2"] = CharacterState(EntityId("c2"), exists=True)
    ws.relationships[("c1", "c2")] = RelationshipState(
        EntityId("c1"),
        EntityId("c2"),
        RelationshipType.ALLY,
        active=False,
        started_at=50,
    )

    graph = TemporalGraphBuilder.build(ws, get_static_entities())

    assert not any(e.source_id == "c1" and e.target_id == "c2" for e in graph.edges)
