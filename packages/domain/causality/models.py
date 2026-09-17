"""Causal Intelligence Domain Models and Contracts (Phase 5.2).

Defines:
- CausalRelationType: Closed enum of causal edge semantics.
- CausalDerivationType: Explicit classification of derivation path.
- CausalConfidence: Deterministic confidence classification.
- CausalEvidenceReference: Provenance tracking for causal edges.
- CausalRelation: Directed causal relation between source and target events.
- CausalChain: Deterministic sequence of connected causal edges.
- CausalConflict: Conflicting or contradictory causal inferences.
- CausalGraphNode: Node in the causal graph.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CausalRelationType(StrEnum):
    """Closed enum of supported causal relation semantics."""

    DIRECT_CAUSE = "DIRECT_CAUSE"
    INDIRECT_INFLUENCE = "INDIRECT_INFLUENCE"
    STATE_TRANSITION = "STATE_TRANSITION"
    RELATIONSHIP_CONSEQUENCE = "RELATIONSHIP_CONSEQUENCE"
    POWER_CONSEQUENCE = "POWER_CONSEQUENCE"
    FACTION_CONSEQUENCE = "FACTION_CONSEQUENCE"
    CHARACTER_CONSEQUENCE = "CHARACTER_CONSEQUENCE"
    EVENT_CHAIN = "EVENT_CHAIN"


class CausalDerivationType(StrEnum):
    """Explicit classification of how the causal relation was derived."""

    CANONICAL_EXPLICIT = "CANONICAL_EXPLICIT"
    DERIVED_DIRECT = "DERIVED_DIRECT"
    DERIVED_INDIRECT = "DERIVED_INDIRECT"
    DERIVED_PROPAGATED = "DERIVED_PROPAGATED"


class CausalConfidence(StrEnum):
    """Deterministic classification of causal confidence."""

    EXPLICIT = "EXPLICIT"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class CausalConflictStatus(StrEnum):
    """Resolution status for conflicting causal evidence."""

    UNRESOLVED = "UNRESOLVED"
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class CausalEvidenceReference:
    """Provenance and analytical basis for a causal relation."""

    rule_id: str
    explanation_code: str
    source_event_ids: tuple[str, ...]
    target_event_id: str
    temporal_basis: str
    state_basis: str | None = None
    relationship_basis: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "explanation_code": self.explanation_code,
            "source_event_ids": list(self.source_event_ids),
            "target_event_id": self.target_event_id,
            "temporal_basis": self.temporal_basis,
            "state_basis": self.state_basis,
            "relationship_basis": self.relationship_basis,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CausalRelation:
    """Represents a single directed causal relation from source to target event."""

    relation_id: str
    series_id: str
    source_event_id: str
    target_event_id: str
    relation_type: CausalRelationType
    derivation_type: CausalDerivationType
    confidence: CausalConfidence
    source_chapter: int
    target_chapter: int
    evidence: CausalEvidenceReference
    impact_score: float = 1.0
    affected_entity_ids: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "relation_id": self.relation_id,
            "series_id": self.series_id,
            "source_event_id": self.source_event_id,
            "target_event_id": self.target_event_id,
            "relation_type": self.relation_type.value,
            "derivation_type": self.derivation_type.value,
            "confidence": self.confidence.value,
            "source_chapter": self.source_chapter,
            "target_chapter": self.target_chapter,
            "impact_score": round(self.impact_score, 4),
            "affected_entity_ids": list(self.affected_entity_ids),
            "evidence": self.evidence.to_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CausalChain:
    """Ordered multi-hop causal chain through the causal graph."""

    chain_id: str
    series_id: str
    origin_event_id: str
    terminal_event_id: str
    start_chapter: int
    end_chapter: int
    relations: tuple[CausalRelation, ...]
    event_ids: tuple[str, ...]
    cumulative_impact_score: float
    depth: int
    confidence: CausalConfidence

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "series_id": self.series_id,
            "origin_event_id": self.origin_event_id,
            "terminal_event_id": self.terminal_event_id,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "depth": self.depth,
            "cumulative_impact_score": round(self.cumulative_impact_score, 4),
            "confidence": self.confidence.value,
            "event_ids": list(self.event_ids),
            "relations": [r.to_dict() for r in self.relations],
        }


@dataclass(frozen=True)
class CausalConflict:
    """Deterministic representation of contradictory causal evidence."""

    conflict_id: str
    series_id: str
    target_event_id: str
    conflicting_relation_ids: tuple[str, ...]
    conflict_type: str
    evidence_summary: str
    resolution_status: CausalConflictStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "series_id": self.series_id,
            "target_event_id": self.target_event_id,
            "conflicting_relation_ids": list(self.conflicting_relation_ids),
            "conflict_type": self.conflict_type,
            "evidence_summary": self.evidence_summary,
            "resolution_status": self.resolution_status.value,
        }
