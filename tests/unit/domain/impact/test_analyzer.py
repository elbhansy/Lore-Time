from packages.domain.entities.event import Event
from packages.domain.impact.impact_type import ImpactType
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_impact_analyzer import EventImpactAnalyzer
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_event_impact_analyzer_character_introduced():
    analyzer = EventImpactAnalyzer(EventApplier())

    before = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))

    e1 = Event(
        id=EntityId("evt1"),
        chapter_id=EntityId("c1"),
        sequence=1,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId("char1"),
        target_type=None,
        target_id=None,
        previous_state={},
        new_state={"name": "A"},
        metadata={"chapter_number": 55},
    )

    res = analyzer.analyze(e1, before)
    assert res.event_id == "evt1"
    assert res.chapter == 55
    assert len(res.impacts) == 1

    imp = res.impacts[0]
    assert imp.impact_type == ImpactType.DIRECT
    assert imp.affected_entity_id == "char1"
    assert imp.description_key == "CHARACTER_INTRODUCED"


def test_event_impact_analyzer_relationship_ended():
    analyzer = EventImpactAnalyzer(EventApplier())

    before = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))
    # We must seed the before state manually or via applier.
    # To end a relationship, it must exist.
    from packages.domain.state.relationship_state import RelationshipState
    from packages.domain.value_objects.relationship_type import RelationshipType

    before.relationships[("A", "B")] = RelationshipState(
        EntityId("A"), EntityId("B"), RelationshipType.ALLY, True, 10
    )

    e1 = Event(
        id=EntityId("evt1"),
        chapter_id=EntityId("c1"),
        sequence=1,
        type=EventType.RELATIONSHIP_ENDED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId("A"),
        target_type=EntityType.CHARACTER,
        target_id=EntityId("B"),
        previous_state={},
        new_state={},
        metadata={"chapter_number": 55},
    )

    res = analyzer.analyze(e1, before)
    assert len(res.impacts) == 1

    imp = res.impacts[0]
    assert imp.impact_type == ImpactType.DIRECT
    assert imp.affected_entity_id == "A->B"
    assert imp.description_key == "RELATIONSHIP_ENDED"
