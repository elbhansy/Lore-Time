"""Unit tests for Causal Intelligence Domain Layer (Phase 5.2 Milestones 5.2.1 - 5.2.16)."""

import uuid

import pytest

from packages.domain.causality.causal_graph import CausalGraph
from packages.domain.causality.chain_builder import CausalChainBuilder
from packages.domain.causality.exceptions import (
    CrossSeriesCausalityError,
    InvalidTemporalCausalityError,
)
from packages.domain.causality.models import (
    CausalConfidence,
    CausalDerivationType,
    CausalEvidenceReference,
    CausalRelation,
    CausalRelationType,
)
from packages.domain.causality.temporal_validator import TemporalCausalValidator
from packages.domain.entities.event import Event
from packages.domain.services.causal_intelligence_service import (
    CausalIntelligenceService,
)
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


def test_causal_domain_models_immutability():
    ev = CausalEvidenceReference(
        rule_id="RULE_TEST",
        explanation_code="EXPLANATION_TEST",
        source_event_ids=("ev1",),
        target_event_id="ev2",
        temporal_basis="Ch 1 <= Ch 2",
    )
    rel = CausalRelation(
        relation_id="rel:1",
        series_id="s1",
        source_event_id="ev1",
        target_event_id="ev2",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        derivation_type=CausalDerivationType.CANONICAL_EXPLICIT,
        confidence=CausalConfidence.EXPLICIT,
        source_chapter=1,
        target_chapter=2,
        evidence=ev,
    )
    assert rel.relation_id == "rel:1"
    with pytest.raises(Exception):
        rel.relation_id = "rel:mutated"


def test_temporal_validator_rejects_retrocausality():
    ev = CausalEvidenceReference(
        rule_id="RULE_TEST",
        explanation_code="EXPLANATION_TEST",
        source_event_ids=("ev2",),
        target_event_id="ev1",
        temporal_basis="Ch 5 > Ch 3",
    )
    rel = CausalRelation(
        relation_id="rel:bad",
        series_id="s1",
        source_event_id="ev2",
        target_event_id="ev1",
        relation_type=CausalRelationType.DIRECT_CAUSE,
        derivation_type=CausalDerivationType.DERIVED_DIRECT,
        confidence=CausalConfidence.STRONG,
        source_chapter=5,
        target_chapter=3,  # Earlier than source!
        evidence=ev,
    )
    with pytest.raises(InvalidTemporalCausalityError):
        TemporalCausalValidator.validate_relation(rel)


def test_temporal_validator_series_isolation():
    with pytest.raises(CrossSeriesCausalityError):
        TemporalCausalValidator.validate_series_isolation("series_A", "series_B")


def test_causal_graph_and_chain_traversal():
    sid = "series_100"
    graph = CausalGraph(series_id=sid)

    # Build A -> B -> C -> D
    ev_a = CausalEvidenceReference("R1", "EXPL", ("A",), "B", "Ch 1 <= Ch 2")
    r_ab = CausalRelation(
        "r_ab",
        sid,
        "A",
        "B",
        CausalRelationType.DIRECT_CAUSE,
        CausalDerivationType.CANONICAL_EXPLICIT,
        CausalConfidence.EXPLICIT,
        1,
        2,
        ev_a,
    )
    ev_b = CausalEvidenceReference("R2", "EXPL", ("B",), "C", "Ch 2 <= Ch 3")
    r_bc = CausalRelation(
        "r_bc",
        sid,
        "B",
        "C",
        CausalRelationType.STATE_TRANSITION,
        CausalDerivationType.DERIVED_DIRECT,
        CausalConfidence.STRONG,
        2,
        3,
        ev_b,
    )
    ev_c = CausalEvidenceReference("R3", "EXPL", ("C",), "D", "Ch 3 <= Ch 4")
    r_cd = CausalRelation(
        "r_cd",
        sid,
        "C",
        "D",
        CausalRelationType.POWER_CONSEQUENCE,
        CausalDerivationType.DERIVED_DIRECT,
        CausalConfidence.STRONG,
        3,
        4,
        ev_c,
    )

    graph.add_relation(r_ab)
    graph.add_relation(r_bc)
    graph.add_relation(r_cd)

    # Downstream from A
    downstream = CausalChainBuilder.build_downstream_chains(graph, "A", max_depth=5)
    assert len(downstream) == 3  # [A->B], [A->B->C], [A->B->C->D]

    deepest = downstream[-1]
    assert deepest.origin_event_id == "A"
    assert deepest.terminal_event_id == "D"
    assert deepest.depth == 3
    assert deepest.event_ids == ("A", "B", "C", "D")

    # Upstream to D
    upstream = CausalChainBuilder.build_upstream_chains(graph, "D", max_depth=5)
    assert len(upstream) == 3  # [C->D], [B->C->D], [A->B->C->D]
    full_up = upstream[-1]
    assert full_up.origin_event_id == "A"
    assert full_up.terminal_event_id == "D"

    # Indirect influence derivation
    indirects = CausalChainBuilder.derive_indirect_relations(graph, max_hops=3)
    # Should derive A->C and A->D, and B->D
    indirect_pairs = [(r.source_event_id, r.target_event_id) for r in indirects]
    assert ("A", "C") in indirect_pairs
    assert ("A", "D") in indirect_pairs
    assert ("B", "D") in indirect_pairs


def test_causal_derivation_from_canonical_events():
    sid = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    e1 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.CHARACTER_INTRODUCED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(char_id)),
    )
    env1 = EventEnvelope(event=e1, chapter_number=ChapterNumber(1))

    e2 = Event(
        id=EntityId.generate(),
        series_id=EntityId(uuid.UUID(sid)),
        chapter_id=EntityId.generate(),
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=EntityId(uuid.UUID(char_id)),
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
        subject_id=EntityId(uuid.UUID(char_id)),
        previous_state={"rank": "E"},
        new_state={"rank": "D"},
        metadata={"cause_event_id": str(e2.id.value)},
    )
    env3 = EventEnvelope(event=e3, chapter_number=ChapterNumber(5))

    service = CausalIntelligenceService()
    graph = service.build_causal_graph(sid, [env1, env2, env3], reader_chapter=5)

    all_rels = graph.get_all_relations()
    assert len(all_rels) >= 2

    # Check that explicit metadata cause was extracted
    explicit_rels = [
        r
        for r in all_rels
        if r.derivation_type == CausalDerivationType.CANONICAL_EXPLICIT
    ]
    assert len(explicit_rels) == 1
    assert explicit_rels[0].source_event_id == str(e2.id.value)
    assert explicit_rels[0].target_event_id == str(e3.id.value)

    # Check character explanation
    explanation = service.explain_character_causality(
        sid, char_id, [env1, env2, env3], reader_chapter=5
    )
    assert explanation.character_id == char_id
    assert len(explanation.central_event_ids) == 3
    assert explanation.summary["total_central_events"] == 3
