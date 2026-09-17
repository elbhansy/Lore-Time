"""Causal Intelligence API Router (Phase 5.2).

Exposes Causal Intelligence endpoints conforming to Phase 5.2 contracts.
"""

import uuid

from fastapi import APIRouter, Depends, Query

from apps.api.app.application.causality.get_character_causality import (
    GetCharacterCausalityUseCase,
)
from apps.api.app.dependencies.services import get_character_causality_use_case
from apps.api.app.schemas.causality import (
    CausalChainDTO,
    CausalEvidenceDTO,
    CausalRelationDTO,
    CharacterCausalExplanationDTO,
)
from packages.domain.causality.character_explainer import CharacterCausalExplanation
from packages.domain.causality.models import (
    CausalChain,
    CausalRelation,
)

router = APIRouter(prefix="/series", tags=["Causal Intelligence"])


def _map_relation_dto(rel: CausalRelation) -> CausalRelationDTO:
    return CausalRelationDTO(
        relation_id=rel.relation_id,
        series_id=rel.series_id,
        source_event_id=rel.source_event_id,
        target_event_id=rel.target_event_id,
        relation_type=rel.relation_type.value,
        derivation_type=rel.derivation_type.value,
        confidence=rel.confidence.value,
        source_chapter=rel.source_chapter,
        target_chapter=rel.target_chapter,
        impact_score=rel.impact_score,
        affected_entity_ids=list(rel.affected_entity_ids),
        evidence=CausalEvidenceDTO(
            rule_id=rel.evidence.rule_id,
            explanation_code=rel.evidence.explanation_code,
            source_event_ids=list(rel.evidence.source_event_ids),
            target_event_id=rel.evidence.target_event_id,
            temporal_basis=rel.evidence.temporal_basis,
            state_basis=rel.evidence.state_basis,
            relationship_basis=rel.evidence.relationship_basis,
            metadata=rel.evidence.metadata,
        ),
        metadata=rel.metadata,
    )


def _map_chain_dto(chain: CausalChain) -> CausalChainDTO:
    return CausalChainDTO(
        chain_id=chain.chain_id,
        series_id=chain.series_id,
        origin_event_id=chain.origin_event_id,
        terminal_event_id=chain.terminal_event_id,
        start_chapter=chain.start_chapter,
        end_chapter=chain.end_chapter,
        depth=chain.depth,
        cumulative_impact_score=chain.cumulative_impact_score,
        confidence=chain.confidence.value,
        event_ids=list(chain.event_ids),
        relations=[_map_relation_dto(r) for r in chain.relations],
    )


@router.get(
    "/{series_id}/intelligence/character-causality/{character_id}",
    response_model=CharacterCausalExplanationDTO,
)
def get_character_causality(
    series_id: uuid.UUID,
    character_id: str,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    max_depth: int = Query(4, ge=1, le=10, description="Maximum causal chain depth"),
    use_case: GetCharacterCausalityUseCase = Depends(get_character_causality_use_case),
):
    """Retrieves deterministic upstream causes and downstream consequences for a character."""
    explanation: CharacterCausalExplanation = use_case.execute(
        series_id=series_id,
        character_id=character_id,
        reader_chapter=chapter,
        max_depth=max_depth,
    )

    return CharacterCausalExplanationDTO(
        character_id=explanation.character_id,
        series_id=explanation.series_id,
        reader_chapter=explanation.reader_chapter,
        central_event_ids=list(explanation.central_event_ids),
        upstream_relations=[
            _map_relation_dto(r) for r in explanation.upstream_relations
        ],
        downstream_relations=[
            _map_relation_dto(r) for r in explanation.downstream_relations
        ],
        upstream_chains=[_map_chain_dto(c) for c in explanation.upstream_chains],
        downstream_chains=[_map_chain_dto(c) for c in explanation.downstream_chains],
        affected_entities=list(explanation.affected_entities),
        summary=explanation.summary,
    )
