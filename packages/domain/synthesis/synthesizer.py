"""Temporal Narrative Causal Synthesis Engine (Phase 5.3).

Synthesizes:
1. Canonical Events & WorldState deltas
2. Character Arc Milestones, Turning Points, and Phases (Phase 5.1)
3. Directed Causal Relations & Multi-Hop Chains (Phase 5.2)

Produces:
- Event Narrative Explanations
- Character Narrative Explanations
- Arc Causal Explanations
"""

from packages.domain.causality.causal_graph import CausalGraph
from packages.domain.causality.chain_builder import CausalChainBuilder
from packages.domain.causality.models import (
    CausalRelation,
    CausalRelationType,
)
from packages.domain.narrative.models import (
    ArcMilestone,
    CharacterArc,
    NarrativePhase,
    TurningPoint,
)
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.synthesis.models import (
    NarrativeCausalPath,
    NarrativeCausalStep,
    NarrativeExplanationType,
    NarrativeImpactDimension,
    TemporalNarrativeCausalExplanation,
    TurningPointSynthesis,
)


class NarrativeCausalSynthesizer:
    """Core synthesis engine mapping causal dynamics to narrative consequences."""

    @classmethod
    def synthesize_event_explanation(
        cls,
        series_id: str,
        event_id: str,
        reader_chapter: int,
        graph: CausalGraph,
        envelopes: list[EventEnvelope],
        arcs_by_character: dict[str, CharacterArc],
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
        """Constructs a deterministic narrative causal explanation centered on an event."""
        # Index envelopes
        env_map = {
            str(e.event.id.value): e
            for e in envelopes
            if e.chapter_number.value <= reader_chapter
        }
        target_env = env_map.get(event_id)
        if not target_env:
            raise ValueError(
                f"Event {event_id} not found in visible timeline up to chapter {reader_chapter}"
            )

        ev = target_env.event
        ch_num = target_env.chapter_number.value

        # Upstream causes & downstream effects
        upstream_chains = CausalChainBuilder.build_upstream_chains(
            graph, event_id, max_depth=max_depth
        )
        downstream_chains = CausalChainBuilder.build_downstream_chains(
            graph, event_id, max_depth=max_depth
        )
        incoming_rels = graph.get_incoming_relations(event_id)
        outgoing_rels = graph.get_outgoing_relations(event_id)

        # Cross-reference with Character Arcs
        milestones_by_event: dict[str, list[ArcMilestone]] = {}
        turning_points_by_event: dict[str, list[TurningPoint]] = {}

        for char_id, arc in arcs_by_character.items():
            for m in arc.milestones:
                milestones_by_event.setdefault(m.event_id, []).append(m)
            for tp in arc.turning_points:
                turning_points_by_event.setdefault(tp.event_id, []).append(tp)

        # Build Narrative Steps
        steps: list[NarrativeCausalStep] = []
        all_relevant_rels = incoming_rels + outgoing_rels
        seen_step_ids: set[str] = set()

        impact_counts: dict[str, int] = {
            dim.value: 0 for dim in NarrativeImpactDimension
        }

        for rel in all_relevant_rels:
            step_id = f"step:{rel.relation_id}"
            if step_id in seen_step_ids:
                continue
            seen_step_ids.add(step_id)

            dims = cls._classify_impact_dimensions(
                rel, milestones_by_event, turning_points_by_event
            )
            for d in dims:
                impact_counts[d.value] += 1

            # Match milestones/turning points
            ms_list = milestones_by_event.get(rel.target_event_id, [])
            tp_list = turning_points_by_event.get(rel.target_event_id, [])

            step = NarrativeCausalStep(
                step_id=step_id,
                series_id=series_id,
                chapter=rel.target_chapter,
                source_event_id=rel.source_event_id,
                target_event_id=rel.target_event_id,
                relation_type=rel.relation_type,
                derivation_type=rel.derivation_type,
                confidence=rel.confidence,
                affected_entities=rel.affected_entity_ids,
                state_change_summary=f"{rel.relation_type.value} leading to Ch {rel.target_chapter}",
                impact_dimensions=dims,
                arc_milestone_id=ms_list[0].milestone_id if ms_list else None,
                turning_point_id=tp_list[0].turning_point_id if tp_list else None,
                evidence_rule_id=rel.evidence.rule_id if rel.evidence else None,
                explanation_code=rel.evidence.explanation_code
                if rel.evidence
                else None,
            )
            steps.append(step)

        # Sort steps deterministically
        steps.sort(
            key=lambda s: (s.chapter, s.source_event_id, s.target_event_id, s.step_id)
        )

        # Build Narrative Paths from downstream chains
        paths: list[NarrativeCausalPath] = []
        for chain in downstream_chains:
            path_steps = []
            path_dims: set[NarrativeImpactDimension] = set()
            for r in chain.relations:
                p_dims = cls._classify_impact_dimensions(
                    r, milestones_by_event, turning_points_by_event
                )
                path_dims.update(p_dims)
                path_steps.append(
                    NarrativeCausalStep(
                        step_id=f"path_step:{r.relation_id}",
                        series_id=series_id,
                        chapter=r.target_chapter,
                        source_event_id=r.source_event_id,
                        target_event_id=r.target_event_id,
                        relation_type=r.relation_type,
                        derivation_type=r.derivation_type,
                        confidence=r.confidence,
                        affected_entities=r.affected_entity_ids,
                        state_change_summary=f"{r.relation_type.value} at Ch {r.target_chapter}",
                        impact_dimensions=p_dims,
                    )
                )

            paths.append(
                NarrativeCausalPath(
                    path_id=f"path:{chain.chain_id}",
                    series_id=series_id,
                    root_event_id=chain.origin_event_id,
                    terminal_event_id=chain.terminal_event_id,
                    start_chapter=chain.start_chapter,
                    end_chapter=chain.end_chapter,
                    steps=tuple(path_steps),
                    cumulative_impact_score=chain.cumulative_impact_score,
                    depth=chain.depth,
                    impact_dimensions=tuple(sorted(list(path_dims))),
                )
            )

        paths.sort(
            key=lambda p: (p.depth, p.end_chapter, p.terminal_event_id, p.path_id)
        )

        # Turning Point Syntheses
        tp_syntheses: list[TurningPointSynthesis] = []
        intersected_milestones: list[str] = []

        for eid in [event_id] + [r.target_event_id for r in outgoing_rels]:
            for tp in turning_points_by_event.get(eid, []):
                char_arc = arcs_by_character.get(tp.character_id)
                p_before, p_after = cls._resolve_phases_around_turning_point(
                    char_arc, tp
                )
                root_causes = tuple(
                    sorted(list({r.source_event_id for r in incoming_rels}))
                )
                down_effects = tuple(
                    sorted(list({r.target_event_id for r in outgoing_rels}))
                )

                tp_syntheses.append(
                    TurningPointSynthesis(
                        turning_point_id=tp.turning_point_id,
                        character_id=tp.character_id,
                        chapter=tp.chapter,
                        trigger_event_id=tp.event_id,
                        turning_point_type=tp.turning_point_type.value,
                        significance=tp.significance.value,
                        before_state=tp.previous_state,
                        after_state=tp.resulting_state,
                        phase_before_id=p_before.phase_id if p_before else None,
                        phase_after_id=p_after.phase_id if p_after else None,
                        causal_root_event_ids=root_causes,
                        downstream_effect_event_ids=down_effects,
                        narrative_impact_summary=f"Turning point '{tp.turning_point_type.value}' triggered at Ch {tp.chapter}",
                    )
                )

            for ms in milestones_by_event.get(eid, []):
                intersected_milestones.append(ms.milestone_id)

        headline = f"Event {ev.type.value} at Chapter {ch_num} (Caused by {len(incoming_rels)}, Propagated to {len(outgoing_rels)} effects)"

        summary = {
            "event_id": event_id,
            "chapter": ch_num,
            "total_upstream_causes": len(incoming_rels),
            "total_downstream_effects": len(outgoing_rels),
            "total_narrative_paths": len(paths),
            "total_turning_points_triggered": len(tp_syntheses),
        }

        return TemporalNarrativeCausalExplanation(
            explanation_id=f"exp:event:{series_id}:{event_id}:ch{reader_chapter}",
            series_id=series_id,
            explanation_type=NarrativeExplanationType.EVENT_NARRATIVE,
            reader_chapter=reader_chapter,
            focus_id=event_id,
            headline=headline,
            narrative_steps=tuple(steps),
            narrative_paths=tuple(paths),
            turning_point_syntheses=tuple(tp_syntheses),
            intersected_milestone_ids=tuple(sorted(list(set(intersected_milestones)))),
            conflicts=tuple(graph.find_contradictions()),
            impact_breakdown=impact_counts,
            summary=summary,
        )

    @classmethod
    def synthesize_character_explanation(
        cls,
        series_id: str,
        character_id: str,
        reader_chapter: int,
        graph: CausalGraph,
        character_arc: CharacterArc,
        envelopes: list[EventEnvelope],
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
        """Constructs a deterministic narrative explanation of a character's arc evolution and causal triggers."""
        # Find all central events
        char_events = [
            e
            for e in envelopes
            if e.chapter_number.value <= reader_chapter
            and (
                (e.event.subject_id and str(e.event.subject_id.value) == character_id)
                or (e.event.target_id and str(e.event.target_id.value) == character_id)
            )
        ]
        central_event_ids = {str(e.event.id.value) for e in char_events}

        milestones_by_event: dict[str, list[ArcMilestone]] = {}
        turning_points_by_event: dict[str, list[TurningPoint]] = {}
        for m in character_arc.milestones:
            milestones_by_event.setdefault(m.event_id, []).append(m)
        for tp in character_arc.turning_points:
            turning_points_by_event.setdefault(tp.event_id, []).append(tp)

        steps: list[NarrativeCausalStep] = []
        paths: list[NarrativeCausalPath] = []
        tp_syntheses: list[TurningPointSynthesis] = []
        impact_counts: dict[str, int] = {
            dim.value: 0 for dim in NarrativeImpactDimension
        }

        # Analyze each turning point
        for tp in character_arc.turning_points:
            up_chains = CausalChainBuilder.build_upstream_chains(
                graph, tp.event_id, max_depth=max_depth
            )
            down_chains = CausalChainBuilder.build_downstream_chains(
                graph, tp.event_id, max_depth=max_depth
            )

            p_before, p_after = cls._resolve_phases_around_turning_point(
                character_arc, tp
            )
            roots = tuple(sorted(list({c.origin_event_id for c in up_chains})))
            effects = tuple(sorted(list({c.terminal_event_id for c in down_chains})))

            tp_syntheses.append(
                TurningPointSynthesis(
                    turning_point_id=tp.turning_point_id,
                    character_id=character_id,
                    chapter=tp.chapter,
                    trigger_event_id=tp.event_id,
                    turning_point_type=tp.turning_point_type.value,
                    significance=tp.significance.value,
                    before_state=tp.previous_state,
                    after_state=tp.resulting_state,
                    phase_before_id=p_before.phase_id if p_before else None,
                    phase_after_id=p_after.phase_id if p_after else None,
                    causal_root_event_ids=roots,
                    downstream_effect_event_ids=effects,
                    narrative_impact_summary=f"Turning point '{tp.turning_point_type.value}' triggered at Ch {tp.chapter} altering arc progression.",
                )
            )

            # Build narrative steps from upstream relations
            for rel in graph.get_incoming_relations(tp.event_id):
                dims = cls._classify_impact_dimensions(
                    rel, milestones_by_event, turning_points_by_event
                )
                for d in dims:
                    impact_counts[d.value] += 1

                steps.append(
                    NarrativeCausalStep(
                        step_id=f"step:{rel.relation_id}",
                        series_id=series_id,
                        chapter=rel.target_chapter,
                        source_event_id=rel.source_event_id,
                        target_event_id=rel.target_event_id,
                        relation_type=rel.relation_type,
                        derivation_type=rel.derivation_type,
                        confidence=rel.confidence,
                        affected_entities=rel.affected_entity_ids,
                        state_change_summary=f"Causal antecedent to turning point {tp.turning_point_id}",
                        impact_dimensions=dims,
                        turning_point_id=tp.turning_point_id,
                    )
                )

        steps.sort(
            key=lambda s: (s.chapter, s.source_event_id, s.target_event_id, s.step_id)
        )
        headline = f"Character Arc Narrative Causal Synthesis for Character {character_id} ({len(character_arc.turning_points)} turning points, {len(character_arc.milestones)} milestones)"

        summary = {
            "character_id": character_id,
            "reader_chapter": reader_chapter,
            "total_milestones": len(character_arc.milestones),
            "total_turning_points": len(character_arc.turning_points),
            "total_phases": len(character_arc.phases),
            "current_status": character_arc.trajectory.current_status
            if character_arc.trajectory
            else "unknown",
        }

        return TemporalNarrativeCausalExplanation(
            explanation_id=f"exp:char:{series_id}:{character_id}:ch{reader_chapter}",
            series_id=series_id,
            explanation_type=NarrativeExplanationType.CHARACTER_NARRATIVE,
            reader_chapter=reader_chapter,
            focus_id=character_id,
            headline=headline,
            narrative_steps=tuple(steps),
            narrative_paths=tuple(paths),
            turning_point_syntheses=tuple(tp_syntheses),
            intersected_milestone_ids=tuple(
                m.milestone_id for m in character_arc.milestones
            ),
            conflicts=tuple(graph.find_contradictions()),
            impact_breakdown=impact_counts,
            summary=summary,
        )

    @staticmethod
    def _classify_impact_dimensions(
        rel: CausalRelation,
        ms_map: dict[str, list[ArcMilestone]],
        tp_map: dict[str, list[TurningPoint]],
    ) -> tuple[NarrativeImpactDimension, ...]:
        dims: set[NarrativeImpactDimension] = {NarrativeImpactDimension.TEMPORAL_IMPACT}

        if rel.relation_type == CausalRelationType.STATE_TRANSITION:
            dims.add(NarrativeImpactDimension.STATE_IMPACT)
            dims.add(NarrativeImpactDimension.CHARACTER_IMPACT)
        elif rel.relation_type == CausalRelationType.RELATIONSHIP_CONSEQUENCE:
            dims.add(NarrativeImpactDimension.RELATIONSHIP_IMPACT)
        elif rel.relation_type == CausalRelationType.POWER_CONSEQUENCE:
            dims.add(NarrativeImpactDimension.POWER_IMPACT)
        elif rel.relation_type == CausalRelationType.FACTION_CONSEQUENCE:
            dims.add(NarrativeImpactDimension.FACTION_IMPACT)

        if rel.target_event_id in ms_map or rel.target_event_id in tp_map:
            dims.add(NarrativeImpactDimension.ARC_IMPACT)

        return tuple(sorted(list(dims)))

    @staticmethod
    def _resolve_phases_around_turning_point(
        arc: CharacterArc | None,
        tp: TurningPoint,
    ) -> tuple[NarrativePhase | None, NarrativePhase | None]:
        if not arc or not arc.phases:
            return None, None

        phase_before = None
        phase_after = None

        for p in arc.phases:
            if p.to_chapter == tp.chapter or (
                p.from_chapter <= tp.chapter <= p.to_chapter
            ):
                phase_before = p
            elif p.from_chapter == tp.chapter + 1:
                phase_after = p

        return phase_before, phase_after
