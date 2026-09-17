"""Pydantic Transport DTOs for Causal Intelligence (Phase 5.2)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CausalEvidenceDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str
    explanation_code: str
    source_event_ids: list[str]
    target_event_id: str
    temporal_basis: str
    state_basis: str | None = None
    relationship_basis: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CausalRelationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    relation_id: str
    series_id: str
    source_event_id: str
    target_event_id: str
    relation_type: str
    derivation_type: str
    confidence: str
    source_chapter: int
    target_chapter: int
    impact_score: float
    affected_entity_ids: list[str]
    evidence: CausalEvidenceDTO
    metadata: dict[str, Any] = Field(default_factory=dict)


class CausalChainDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    chain_id: str
    series_id: str
    origin_event_id: str
    terminal_event_id: str
    start_chapter: int
    end_chapter: int
    depth: int
    cumulative_impact_score: float
    confidence: str
    event_ids: list[str]
    relations: list[CausalRelationDTO]


class CharacterCausalExplanationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    character_id: str
    series_id: str
    reader_chapter: int
    central_event_ids: list[str]
    upstream_relations: list[CausalRelationDTO]
    downstream_relations: list[CausalRelationDTO]
    upstream_chains: list[CausalChainDTO]
    downstream_chains: list[CausalChainDTO]
    affected_entities: list[str]
    summary: dict[str, Any]
