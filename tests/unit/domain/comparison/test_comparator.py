from packages.domain.comparison.character_diff import ChangeType
from packages.domain.comparison.relationship_diff import RelationshipChangeType
from packages.domain.comparison.world_state_comparator import WorldStateComparator
from packages.domain.state.character_state import CharacterState
from packages.domain.state.relationship_state import RelationshipState
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.relationship_type import RelationshipType


def test_comparator_character_introduced():
    w1 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))

    w2 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    w2.characters["c1"] = CharacterState(
        character_id=EntityId("c1"), exists=True, alive=True
    )

    comp = WorldStateComparator.compare(w1, w2)
    assert len(comp.character_changes) == 1
    assert comp.character_changes[0].change_type == ChangeType.INTRODUCED
    assert comp.character_changes[0].character_id == "c1"


def test_comparator_power_changed():
    w1 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))
    w1.characters["c1"] = CharacterState(
        character_id=EntityId("c1"), exists=True, alive=True, rank="B"
    )

    w2 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    w2.characters["c1"] = CharacterState(
        character_id=EntityId("c1"), exists=True, alive=True, rank="S"
    )

    comp = WorldStateComparator.compare(w1, w2)
    assert len(comp.power_changes) == 1
    assert comp.power_changes[0].before_rank == "B"
    assert comp.power_changes[0].after_rank == "S"


def test_comparator_relationship_changed():
    w1 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))
    w1.relationships[("A", "B")] = RelationshipState(
        subject_id=EntityId("A"),
        target_id=EntityId("B"),
        relationship_type=RelationshipType.ALLY,
        active=True,
        started_at=10,
    )

    w2 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    w2.relationships[("A", "B")] = RelationshipState(
        subject_id=EntityId("A"),
        target_id=EntityId("B"),
        relationship_type=RelationshipType.ENEMY,
        active=True,
        started_at=10,
    )

    comp = WorldStateComparator.compare(w1, w2)
    assert len(comp.relationship_changes) == 1
    assert comp.relationship_changes[0].change_type == RelationshipChangeType.CHANGED
    assert comp.relationship_changes[0].before_type == "ALLY"
    assert comp.relationship_changes[0].after_type == "ENEMY"


def test_comparator_skills_unlocked():
    w1 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(50))
    w1.characters["c1"] = CharacterState(
        character_id=EntityId("c1"),
        exists=True,
        alive=True,
        unlocked_skills={"Fireball"},
    )

    w2 = WorldState(series_id=EntityId("s1"), chapter=ChapterNumber(100))
    w2.characters["c1"] = CharacterState(
        character_id=EntityId("c1"),
        exists=True,
        alive=True,
        unlocked_skills={"Fireball", "Lightning"},
    )

    comp = WorldStateComparator.compare(w1, w2)
    assert len(comp.skill_changes) == 1
    assert comp.skill_changes[0].unlocked_skills == ["Lightning"]
