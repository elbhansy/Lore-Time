"""Deterministic Causal Derivation Engine (Phase 5.2 Milestones 5.2.3, 5.2.8 - 5.2.11).

Derives directed CausalRelation edges from visible canonical event envelopes and WorldState:
1. Pattern A: Explicit Canonical Causality (cause_event_id in event.metadata).
2. Pattern B: Character State Transitions & Consequences (e.g. Introduction -> Actions, Rank Change -> Power Consequence, Death).
3. Pattern C: Relationship Transitions & Propagation (Formation -> Changed -> Severed).
4. Pattern D: Faction Succession & Affiliation Shifts (Joined -> Leadership -> Left).
5. Pattern E: Power & Skill Consequences (Unlocked -> Evolved / Combined).

All relations are attached to structured, deterministic CausalEvidenceReference objects.
"""

from packages.domain.causality.impact_scorer import compute_causal_impact_score
from packages.domain.causality.models import (
    CausalConfidence,
    CausalDerivationType,
    CausalEvidenceReference,
    CausalRelation,
    CausalRelationType,
)
from packages.domain.causality.temporal_validator import TemporalCausalValidator
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.event_type import EventType


class CausalDerivationEngine:
    """Derives deterministic causal relationships from canonical events."""

    @classmethod
    def derive_relations(
        cls,
        series_id: str,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        reader_chapter: int | None = None,
    ) -> list[CausalRelation]:
        """Extracts and validates all supported deterministic causal relations."""
        # 1. Filter envelopes by reader_chapter firewall
        visible_envelopes = [
            env
            for env in envelopes
            if reader_chapter is None or env.chapter_number.value <= reader_chapter
        ]

        # 2. Sort visible envelopes deterministically: chapter -> sequence -> id
        sorted_envelopes = sorted(
            visible_envelopes,
            key=lambda env: (
                env.chapter_number.value,
                env.event.sequence,
                str(env.event.id.value),
            ),
        )

        relations: list[CausalRelation] = []

        # Index envelopes by event_id string
        envelope_by_id = {str(env.event.id.value): env for env in sorted_envelopes}

        # Sub-indices for deterministic entity tracking
        events_by_subject: dict[str, list[EventEnvelope]] = {}
        events_by_target: dict[str, list[EventEnvelope]] = {}
        events_by_entity: dict[str, list[EventEnvelope]] = {}

        for env in sorted_envelopes:
            s_id = str(env.event.subject_id.value) if env.event.subject_id else None
            t_id = str(env.event.target_id.value) if env.event.target_id else None

            if s_id:
                events_by_subject.setdefault(s_id, []).append(env)
                events_by_entity.setdefault(s_id, []).append(env)
            if t_id:
                events_by_target.setdefault(t_id, []).append(env)
                events_by_entity.setdefault(t_id, []).append(env)

        # -------------------------------------------------------------
        # Rule 1: Explicit Canonical Causality (metadata['cause_event_id'])
        # -------------------------------------------------------------
        for env in sorted_envelopes:
            target_ev = env.event
            target_id_str = str(target_ev.id.value)
            cause_id = target_ev.metadata.get(
                "cause_event_id"
            ) or target_ev.metadata.get("caused_by_event_id")

            if cause_id and str(cause_id) in envelope_by_id:
                cause_env = envelope_by_id[str(cause_id)]
                cause_ev = cause_env.event

                affected_entities = tuple(
                    sorted(
                        {
                            str(target_ev.subject_id.value)
                            if target_ev.subject_id
                            else None,
                            str(target_ev.target_id.value)
                            if target_ev.target_id
                            else None,
                            str(cause_ev.subject_id.value)
                            if cause_ev.subject_id
                            else None,
                        }
                        - {None}
                    )
                )

                evidence = CausalEvidenceReference(
                    rule_id="RULE_CANONICAL_EXPLICIT",
                    explanation_code="EXPLICIT_CAUSE_METADATA",
                    source_event_ids=(str(cause_ev.id.value),),
                    target_event_id=target_id_str,
                    temporal_basis=f"Ch {cause_env.chapter_number.value} <= Ch {env.chapter_number.value}",
                    state_basis="explicit_canonical_link",
                )

                rel = CausalRelation(
                    relation_id=f"causal:{series_id}:{cause_ev.id.value}:{target_id_str}:explicit",
                    series_id=series_id,
                    source_event_id=str(cause_ev.id.value),
                    target_event_id=target_id_str,
                    relation_type=CausalRelationType.DIRECT_CAUSE,
                    derivation_type=CausalDerivationType.CANONICAL_EXPLICIT,
                    confidence=CausalConfidence.EXPLICIT,
                    source_chapter=cause_env.chapter_number.value,
                    target_chapter=env.chapter_number.value,
                    evidence=evidence,
                    impact_score=compute_causal_impact_score(
                        CausalRelationType.DIRECT_CAUSE,
                        CausalConfidence.EXPLICIT,
                        len(affected_entities),
                        is_critical_transition=(
                            target_ev.type == EventType.CHARACTER_DIED
                        ),
                    ),
                    affected_entity_ids=affected_entities,
                )
                relations.append(rel)

        # -------------------------------------------------------------
        # Rule 2: State Transitions & Character Propagation
        # An event modifying a character's state directly enables/causes their subsequent state changes.
        # e.g., CHARACTER_INTRODUCED -> subsequent state changes
        # e.g., POWER_RANK_CHANGED -> subsequent rank change
        # -------------------------------------------------------------
        for entity_id, entity_envs in events_by_subject.items():
            for i in range(len(entity_envs) - 1):
                prev_env = entity_envs[i]
                next_env = entity_envs[i + 1]

                prev_ev = prev_env.event
                next_ev = next_env.event

                # Direct character lifecycle / power progression link
                is_lifecycle = (
                    prev_ev.type == EventType.CHARACTER_INTRODUCED
                    or next_ev.type == EventType.CHARACTER_DIED
                )
                is_rank_progression = (
                    prev_ev.type == EventType.POWER_RANK_CHANGED
                    and next_ev.type == EventType.POWER_RANK_CHANGED
                )
                is_skill_evolution = prev_ev.type in (
                    EventType.SKILL_UNLOCKED,
                    EventType.SKILL_UPGRADED,
                ) and next_ev.type in (
                    EventType.SKILL_UPGRADED,
                    EventType.SKILL_EVOLVED,
                    EventType.SKILL_COMBINED,
                )

                if is_lifecycle or is_rank_progression or is_skill_evolution:
                    rel_type = (
                        CausalRelationType.STATE_TRANSITION
                        if is_lifecycle
                        else (
                            CausalRelationType.POWER_CONSEQUENCE
                            if (is_rank_progression or is_skill_evolution)
                            else CausalRelationType.CHARACTER_CONSEQUENCE
                        )
                    )

                    confidence = (
                        CausalConfidence.STRONG
                        if (is_lifecycle or is_rank_progression)
                        else CausalConfidence.MODERATE
                    )

                    rule_id = (
                        "RULE_CHARACTER_LIFECYCLE"
                        if is_lifecycle
                        else (
                            "RULE_POWER_PROGRESSION"
                            if is_rank_progression
                            else "RULE_SKILL_EVOLUTION"
                        )
                    )

                    evidence = CausalEvidenceReference(
                        rule_id=rule_id,
                        explanation_code=f"{prev_ev.type.value}_TO_{next_ev.type.value}",
                        source_event_ids=(str(prev_ev.id.value),),
                        target_event_id=str(next_ev.id.value),
                        temporal_basis=f"Ch {prev_env.chapter_number.value} <= Ch {next_env.chapter_number.value}",
                        state_basis=f"entity:{entity_id}",
                    )

                    rel = CausalRelation(
                        relation_id=f"causal:{series_id}:{prev_ev.id.value}:{next_ev.id.value}:{rel_type.value.lower()}",
                        series_id=series_id,
                        source_event_id=str(prev_ev.id.value),
                        target_event_id=str(next_ev.id.value),
                        relation_type=rel_type,
                        derivation_type=CausalDerivationType.DERIVED_DIRECT,
                        confidence=confidence,
                        source_chapter=prev_env.chapter_number.value,
                        target_chapter=next_env.chapter_number.value,
                        evidence=evidence,
                        impact_score=compute_causal_impact_score(
                            rel_type,
                            confidence,
                            1,
                            is_critical_transition=(
                                next_ev.type == EventType.CHARACTER_DIED
                            ),
                        ),
                        affected_entity_ids=(entity_id,),
                    )
                    relations.append(rel)

        # -------------------------------------------------------------
        # Rule 3: Relationship Consequence & Transitions
        # Pair-wise relationship evolution: CREATED -> CHANGED -> ENDED
        # -------------------------------------------------------------
        rel_events_by_pair: dict[tuple[str, str], list[EventEnvelope]] = {}
        for env in sorted_envelopes:
            if env.event.type in (
                EventType.RELATIONSHIP_CREATED,
                EventType.RELATIONSHIP_CHANGED,
                EventType.RELATIONSHIP_ENDED,
            ):
                s = str(env.event.subject_id.value) if env.event.subject_id else ""
                t = str(env.event.target_id.value) if env.event.target_id else ""
                if s and t:
                    pair = tuple(sorted([s, t]))
                    rel_events_by_pair.setdefault(pair, []).append(env)

        for (e1_id, e2_id), pair_envs in rel_events_by_pair.items():
            for i in range(len(pair_envs) - 1):
                prev_env = pair_envs[i]
                next_env = pair_envs[i + 1]

                evidence = CausalEvidenceReference(
                    rule_id="RULE_RELATIONSHIP_TRANSITION",
                    explanation_code=f"RELATIONSHIP_{prev_env.event.type.value}_TO_{next_env.event.type.value}",
                    source_event_ids=(str(prev_env.event.id.value),),
                    target_event_id=str(next_env.event.id.value),
                    temporal_basis=f"Ch {prev_env.chapter_number.value} <= Ch {next_env.chapter_number.value}",
                    relationship_basis=f"{e1_id}:{e2_id}",
                )

                rel = CausalRelation(
                    relation_id=f"causal:{series_id}:{prev_env.event.id.value}:{next_env.event.id.value}:rel",
                    series_id=series_id,
                    source_event_id=str(prev_env.event.id.value),
                    target_event_id=str(next_env.event.id.value),
                    relation_type=CausalRelationType.RELATIONSHIP_CONSEQUENCE,
                    derivation_type=CausalDerivationType.DERIVED_DIRECT,
                    confidence=CausalConfidence.STRONG,
                    source_chapter=prev_env.chapter_number.value,
                    target_chapter=next_env.chapter_number.value,
                    evidence=evidence,
                    impact_score=compute_causal_impact_score(
                        CausalRelationType.RELATIONSHIP_CONSEQUENCE,
                        CausalConfidence.STRONG,
                        2,
                    ),
                    affected_entity_ids=(e1_id, e2_id),
                )
                relations.append(rel)

        # -------------------------------------------------------------
        # Rule 4: Faction Affiliation & Leadership Propagation
        # e.g., FACTION_INTRODUCED -> FACTION_MEMBER_JOINED -> FACTION_LEADER_CHANGED -> FACTION_MEMBER_LEFT
        # -------------------------------------------------------------
        faction_events_by_faction: dict[str, list[EventEnvelope]] = {}
        for env in sorted_envelopes:
            if env.event.type in (
                EventType.FACTION_INTRODUCED,
                EventType.FACTION_MEMBER_JOINED,
                EventType.FACTION_MEMBER_LEFT,
                EventType.FACTION_LEADER_CHANGED,
            ):
                # subject is faction in INTRODUCED and LEADER_CHANGED; target in JOINED / LEFT
                fac_id = None
                if env.event.type in (
                    EventType.FACTION_INTRODUCED,
                    EventType.FACTION_LEADER_CHANGED,
                ):
                    fac_id = (
                        str(env.event.subject_id.value)
                        if env.event.subject_id
                        else None
                    )
                else:
                    fac_id = (
                        str(env.event.target_id.value) if env.event.target_id else None
                    )

                if fac_id:
                    faction_events_by_faction.setdefault(fac_id, []).append(env)

        for fac_id, fac_envs in faction_events_by_faction.items():
            for i in range(len(fac_envs) - 1):
                prev_env = fac_envs[i]
                next_env = fac_envs[i + 1]

                evidence = CausalEvidenceReference(
                    rule_id="RULE_FACTION_PROPAGATION",
                    explanation_code=f"FACTION_{prev_env.event.type.value}_TO_{next_env.event.type.value}",
                    source_event_ids=(str(prev_env.event.id.value),),
                    target_event_id=str(next_env.event.id.value),
                    temporal_basis=f"Ch {prev_env.chapter_number.value} <= Ch {next_env.chapter_number.value}",
                    state_basis=f"faction:{fac_id}",
                )

                affected = tuple(
                    sorted(
                        {
                            fac_id,
                            str(prev_env.event.subject_id.value)
                            if prev_env.event.subject_id
                            else None,
                            str(next_env.event.subject_id.value)
                            if next_env.event.subject_id
                            else None,
                        }
                        - {None}
                    )
                )

                rel = CausalRelation(
                    relation_id=f"causal:{series_id}:{prev_env.event.id.value}:{next_env.event.id.value}:faction",
                    series_id=series_id,
                    source_event_id=str(prev_env.event.id.value),
                    target_event_id=str(next_env.event.id.value),
                    relation_type=CausalRelationType.FACTION_CONSEQUENCE,
                    derivation_type=CausalDerivationType.DERIVED_DIRECT,
                    confidence=CausalConfidence.STRONG,
                    source_chapter=prev_env.chapter_number.value,
                    target_chapter=next_env.chapter_number.value,
                    evidence=evidence,
                    impact_score=compute_causal_impact_score(
                        CausalRelationType.FACTION_CONSEQUENCE,
                        CausalConfidence.STRONG,
                        len(affected),
                    ),
                    affected_entity_ids=affected,
                )
                relations.append(rel)

        # -------------------------------------------------------------
        # 3. Validate each generated relation through TemporalCausalValidator
        # -------------------------------------------------------------
        valid_relations: list[CausalRelation] = []
        seen_relation_ids: set[str] = set()

        for rel in relations:
            if rel.relation_id in seen_relation_ids:
                continue
            seen_relation_ids.add(rel.relation_id)

            TemporalCausalValidator.validate_relation(
                rel, reader_chapter=reader_chapter
            )
            valid_relations.append(rel)

        # Sort deterministically: source_chapter -> target_chapter -> source_id -> target_id -> relation_type
        valid_relations.sort(
            key=lambda r: (
                r.source_chapter,
                r.target_chapter,
                r.source_event_id,
                r.target_event_id,
                r.relation_type.value,
                r.relation_id,
            )
        )

        return valid_relations
