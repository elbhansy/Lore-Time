"""Deterministic Causal Impact Scoring (Phase 5.2 Milestone 5.2.12).

Calculates an explainable, deterministic impact score for causal edges and chains:
impact_score = directness_weight * confidence_weight * entity_spread_weight * transition_weight

Where:
- directness_weight:
    DIRECT_CAUSE = 1.0
    STATE_TRANSITION = 0.95
    RELATIONSHIP_CONSEQUENCE = 0.9
    FACTION_CONSEQUENCE = 0.85
    POWER_CONSEQUENCE = 0.85
    CHARACTER_CONSEQUENCE = 0.8
    INDIRECT_INFLUENCE = 0.6
    EVENT_CHAIN = 0.5
- confidence_weight:
    EXPLICIT = 1.0
    STRONG = 0.85
    MODERATE = 0.65
    WEAK = 0.4
- entity_spread_weight:
    min(1.5, 1.0 + (affected_count * 0.1))
- transition_weight:
    Base 1.0, adjusted upwards for mortality (1.5) or rank breakthrough (1.3).
"""

from packages.domain.causality.models import (
    CausalConfidence,
    CausalRelationType,
)

DIRECTNESS_WEIGHTS: dict[CausalRelationType, float] = {
    CausalRelationType.DIRECT_CAUSE: 1.0,
    CausalRelationType.STATE_TRANSITION: 0.95,
    CausalRelationType.RELATIONSHIP_CONSEQUENCE: 0.9,
    CausalRelationType.FACTION_CONSEQUENCE: 0.85,
    CausalRelationType.POWER_CONSEQUENCE: 0.85,
    CausalRelationType.CHARACTER_CONSEQUENCE: 0.8,
    CausalRelationType.INDIRECT_INFLUENCE: 0.6,
    CausalRelationType.EVENT_CHAIN: 0.5,
}

CONFIDENCE_WEIGHTS: dict[CausalConfidence, float] = {
    CausalConfidence.EXPLICIT: 1.0,
    CausalConfidence.STRONG: 0.85,
    CausalConfidence.MODERATE: 0.65,
    CausalConfidence.WEAK: 0.4,
}


def compute_causal_impact_score(
    relation_type: CausalRelationType,
    confidence: CausalConfidence,
    affected_entity_count: int = 1,
    is_critical_transition: bool = False,
) -> float:
    """Computes an explainable, deterministic impact score in range [0.1, 2.5]."""
    directness = DIRECTNESS_WEIGHTS.get(relation_type, 0.7)
    conf = CONFIDENCE_WEIGHTS.get(confidence, 0.7)
    spread = min(1.5, 1.0 + (max(0, affected_entity_count - 1) * 0.1))
    transition = 1.4 if is_critical_transition else 1.0

    raw_score = directness * conf * spread * transition
    return round(raw_score, 4)
