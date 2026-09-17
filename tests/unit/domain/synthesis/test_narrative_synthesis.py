"""Unit tests for Temporal Narrative Causal Synthesis (Phase 5.3)."""

import uuid

from packages.domain.entities.event import Event
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.temporal_narrative_synthesis_service import (
    TemporalNarrativeSynthesisService,
)
from packages.domain.synthesis.models import (
    NarrativeExplanationType,
)
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_event_narrative_synthesis_contracts_and_intersection():
    sid = str(uuid.uuid4())
    cid = str(uuid.uuid4())

    e1 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(cid)),
    )
    env1 = EventEnvelope(event=e1, chapter_number=ChapterNumber(1))

    e2 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(cid)),
        previous_state={"rank": "F"},
        new_state={"rank": "E"},
    )
    env2 = EventEnvelope(event=e2, chapter_number=ChapterNumber(3))

    e3 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(cid)),
        previous_state={"rank": "E"},
        new_state={"rank": "S"},
        metadata={"cause_event_id": str(e2.id.value)},
    )
    env3 = EventEnvelope(event=e3, chapter_number=ChapterNumber(5))

    envelopes = [env1, env2, env3]
    service = TemporalNarrativeSynthesisService()

    # Synthesize for Event 3
    explanation = service.explain_event_narrative(
        series_id=sid,
        event_id=str(e3.id.value),
        reader_chapter=5,
        envelopes=envelopes,
    )

    assert explanation.explanation_type == NarrativeExplanationType.EVENT_NARRATIVE
    assert explanation.focus_id == str(e3.id.value)
    assert explanation.reader_chapter == 5
    assert len(explanation.narrative_steps) >= 1
    assert any(
        s.source_event_id == str(e2.id.value) for s in explanation.narrative_steps
    )


def test_character_narrative_causality_synthesis():
    sid = str(uuid.uuid4())
    cid = str(uuid.uuid4())

    e1 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(cid)),
    )
    env1 = EventEnvelope(event=e1, chapter_number=ChapterNumber(1))

    e2 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(cid)),
        previous_state={"rank": "F"},
        new_state={"rank": "S"},
    )
    env2 = EventEnvelope(event=e2, chapter_number=ChapterNumber(3))

    envelopes = [env1, env2]
    service = TemporalNarrativeSynthesisService()

    explanation = service.explain_character_narrative_causality(
        series_id=sid,
        character_id=cid,
        reader_chapter=3,
        envelopes=envelopes,
    )

    assert explanation.explanation_type == NarrativeExplanationType.CHARACTER_NARRATIVE
    assert explanation.focus_id == cid
    assert len(explanation.turning_point_syntheses) >= 1
    tp_syn = explanation.turning_point_syntheses[0]
    assert tp_syn.character_id == cid
    assert tp_syn.chapter == 3
