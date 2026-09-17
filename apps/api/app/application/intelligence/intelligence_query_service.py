"""Application Query Service for UI Read Models (Phase 5.4).

Orchestrates:
1. StoryOverviewReadModel assembly
2. TimelineReadModel assembly with deterministic pagination
3. EventReadModel assembly with causal causes/effects
4. CharacterReadModel assembly
5. Universal GenericGraphReadModel projection (causal / relationship)
Enforces:
- Temporal Firewall (readerChapter <= N)
- Multi-Tenant Series Isolation
- Bounded traversal & deterministic ordering
"""

import logging
import uuid

from apps.api.app.application.exceptions import (
    CharacterNotFound,
    InvalidChapter,
    SeriesNotFound,
)
from apps.api.app.core.cache import CacheService, get_cache_service
from apps.api.app.schemas.causality import CausalEvidenceDTO, CausalRelationDTO
from apps.api.app.schemas.narrative import (
    ArcMilestoneDTO,
    NarrativePhaseDTO,
    TurningPointDTO,
)
from apps.api.app.schemas.read_models import (
    CharacterReadModel,
    EventReadModel,
    GenericGraphReadModel,
    PaginationMeta,
    StoryOverviewReadModel,
    TemporalContextReadModel,
    TimelineReadModel,
    UniversalGraphEdge,
    UniversalGraphNode,
)
from packages.domain.causality.models import CausalRelation
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.services.causal_intelligence_service import (
    CausalIntelligenceService,
)
from packages.domain.services.narrative_intelligence_engine import (
    NarrativeIntelligenceEngine,
)
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

logger = logging.getLogger("timeline.application")


def _map_rel_dto(r: CausalRelation) -> CausalRelationDTO:
    return CausalRelationDTO(
        relation_id=r.relation_id,
        series_id=r.series_id,
        source_event_id=r.source_event_id,
        target_event_id=r.target_event_id,
        relation_type=r.relation_type.value,
        derivation_type=r.derivation_type.value,
        confidence=r.confidence.value,
        source_chapter=r.source_chapter,
        target_chapter=r.target_chapter,
        impact_score=r.impact_score,
        affected_entity_ids=list(r.affected_entity_ids),
        evidence=CausalEvidenceDTO(
            rule_id=r.evidence.rule_id,
            explanation_code=r.evidence.explanation_code,
            source_event_ids=list(r.evidence.source_event_ids),
            target_event_id=r.evidence.target_event_id,
            temporal_basis=r.evidence.temporal_basis,
            state_basis=r.evidence.state_basis,
            relationship_basis=r.evidence.relationship_basis,
            metadata=r.evidence.metadata,
        ),
        metadata=r.metadata,
    )


def _map_milestone_dto(m) -> ArcMilestoneDTO:
    return ArcMilestoneDTO(
        milestone_id=m.milestone_id,
        character_id=m.character_id,
        chapter=m.chapter,
        sequence=m.sequence,
        event_id=m.event_id,
        milestone_type=m.milestone_type.value,
        description=m.description,
        previous_state=m.previous_state,
        new_state=m.new_state,
        is_canonical=m.is_canonical,
    )


def _map_turning_point_dto(tp) -> TurningPointDTO:
    return TurningPointDTO(
        turning_point_id=tp.turning_point_id,
        character_id=tp.character_id,
        chapter=tp.chapter,
        sequence=tp.sequence,
        event_id=tp.event_id,
        turning_point_type=tp.turning_point_type.value,
        significance=tp.significance.value,
        description=tp.description,
        affected_dimensions=tp.affected_dimensions,
        previous_state=tp.previous_state,
        resulting_state=tp.resulting_state,
        is_analytical=tp.is_analytical,
    )


def _map_phase_dto(p) -> NarrativePhaseDTO:
    return NarrativePhaseDTO(
        phase_id=p.phase_id,
        character_id=p.character_id,
        phase_number=p.phase_number,
        title=p.title,
        from_chapter=p.from_chapter,
        to_chapter=p.to_chapter,
        milestone_ids=p.milestone_ids,
        turning_point_id=p.turning_point_id,
        dominant_faction=p.dominant_faction,
        rank_at_phase_end=p.rank_at_phase_end,
        is_active_at_horizon=p.is_active_at_horizon,
    )


class IntelligenceQueryService:
    """Read service orchestrating UI-facing query models."""

    def __init__(
        self,
        series_repo: SeriesRepository,
        character_repo: CharacterRepository,
        event_repo: EventRepository,
        world_state_builder: WorldStateBuilder,
        narrative_engine: NarrativeIntelligenceEngine,
        causal_service: CausalIntelligenceService,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.character_repo = character_repo
        self.event_repo = event_repo
        self.world_state_builder = world_state_builder
        self.narrative_engine = narrative_engine
        self.causal_service = causal_service
        self.cache_service = cache_service or get_cache_service()

    def get_story_overview(
        self,
        series_id: uuid.UUID,
        reader_chapter: int,
    ) -> StoryOverviewReadModel:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_eid = EntityId(series_id)
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        def compute() -> StoryOverviewReadModel:
            chapter_val = ChapterNumber(reader_chapter)
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )
            world_state = self.world_state_builder.build(
                series_eid, envelopes, chapter_val
            )

            # Discover visible characters
            visible_chars = self.character_repo.get_all_by_series(series_eid)
            all_turning_points: list[TurningPointDTO] = []
            active_phases: dict[str, str] = {}

            for c in visible_chars:
                cid_str = str(c.id.value)
                arc = self.narrative_engine.derive_character_arc(
                    str(series_id), cid_str, reader_chapter, envelopes, world_state
                )
                for tp in arc.turning_points:
                    all_turning_points.append(_map_turning_point_dto(tp))
                if arc.phases:
                    active_phases[cid_str] = arc.phases[-1].title

            # Deterministic sorting
            all_turning_points.sort(
                key=lambda tp: (tp.chapter, tp.sequence, tp.turning_point_id)
            )

            # Recent events (up to 10 most recent)
            sorted_envs = sorted(
                envelopes,
                key=lambda env: (
                    env.chapter_number.value,
                    env.event.sequence,
                    str(env.event.id.value),
                ),
            )
            recent_envs = sorted_envs[-10:] if len(sorted_envs) > 10 else sorted_envs
            recent_events = [
                EventReadModel(
                    event_id=str(env.event.id.value),
                    series_id=str(series_id),
                    chapter_number=env.chapter_number.value,
                    sequence=env.event.sequence,
                    event_type=env.event.type.value,
                    subject_type=env.event.subject_type.value,
                    subject_id=str(env.event.subject_id.value),
                    target_type=env.event.target_type.value
                    if env.event.target_type
                    else None,
                    target_id=str(env.event.target_id.value)
                    if env.event.target_id
                    else None,
                    title=f"Event {env.event.type.value} at Chapter {env.chapter_number.value}",
                    description=f"{env.event.type.value} on {env.event.subject_type.value}",
                    previous_state=env.event.previous_state,
                    new_state=env.event.new_state,
                    metadata=env.event.metadata,
                )
                for env in recent_envs
            ]

            temporal_ctx = TemporalContextReadModel(
                series_id=str(series_id),
                reader_chapter=reader_chapter,
                min_visible_chapter=1,
                max_visible_chapter=reader_chapter,
                future_information_excluded=True,
            )

            return StoryOverviewReadModel(
                series_id=str(series_id),
                series_title=series.title
                if hasattr(series, "title")
                else str(series_id),
                temporal_context=temporal_ctx,
                total_chapters_visible=reader_chapter,
                total_events_visible=len(envelopes),
                total_characters_visible=len(visible_chars),
                total_factions_visible=len(world_state.factions),
                total_relationships_active=sum(
                    1 for r in world_state.relationships.values() if r.active
                ),
                recent_turning_points=all_turning_points[-5:]
                if len(all_turning_points) > 5
                else all_turning_points,
                recent_events=recent_events,
                active_phases_by_character=active_phases,
            )

        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource="read_model:overview",
                compute_fn=compute,
                reader_chapter=reader_chapter,
            )
        return compute()

    def get_timeline(
        self,
        series_id: uuid.UUID,
        reader_chapter: int,
        from_chapter: int = 1,
        to_chapter: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TimelineReadModel:
        if reader_chapter < 1 or from_chapter < 1:
            raise InvalidChapter("Chapter numbers must be positive")

        actual_to = min(reader_chapter, to_chapter or reader_chapter)
        if from_chapter > actual_to:
            actual_to = from_chapter

        series_eid = EntityId(series_id)
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        def compute() -> TimelineReadModel:
            chapter_val = ChapterNumber(actual_to)
            all_envs = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )

            # Filter range [from_chapter, actual_to]
            range_envs = [
                e
                for e in all_envs
                if from_chapter <= e.chapter_number.value <= actual_to
            ]
            range_envs.sort(
                key=lambda env: (
                    env.chapter_number.value,
                    env.event.sequence,
                    str(env.event.id.value),
                )
            )

            total_events = len(range_envs)
            paged_envs = range_envs[offset : offset + limit]

            # Build causal graph to attach causes/effects
            graph = self.causal_service.build_causal_graph(
                str(series_id), all_envs, reader_chapter=actual_to
            )

            paged_events = [
                EventReadModel(
                    event_id=str(env.event.id.value),
                    series_id=str(series_id),
                    chapter_number=env.chapter_number.value,
                    sequence=env.event.sequence,
                    event_type=env.event.type.value,
                    subject_type=env.event.subject_type.value,
                    subject_id=str(env.event.subject_id.value),
                    target_type=env.event.target_type.value
                    if env.event.target_type
                    else None,
                    target_id=str(env.event.target_id.value)
                    if env.event.target_id
                    else None,
                    title=f"Event {env.event.type.value} at Ch {env.chapter_number.value}",
                    description=f"{env.event.type.value} on {env.event.subject_type.value}",
                    previous_state=env.event.previous_state,
                    new_state=env.event.new_state,
                    metadata=env.event.metadata,
                    causes=[
                        _map_rel_dto(r)
                        for r in graph.get_incoming_relations(str(env.event.id.value))
                    ],
                    effects=[
                        _map_rel_dto(r)
                        for r in graph.get_outgoing_relations(str(env.event.id.value))
                    ],
                )
                for env in paged_envs
            ]

            temporal_ctx = TemporalContextReadModel(
                series_id=str(series_id),
                reader_chapter=reader_chapter,
                min_visible_chapter=from_chapter,
                max_visible_chapter=actual_to,
                future_information_excluded=True,
            )

            pagination = PaginationMeta(
                limit=limit,
                offset=offset,
                total_count=total_events,
                has_more=(offset + limit) < total_events,
            )

            return TimelineReadModel(
                temporal_context=temporal_ctx,
                from_chapter=from_chapter,
                to_chapter=actual_to,
                events=paged_events,
                total_events=total_events,
                pagination=pagination,
            )

        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource="read_model:timeline",
                compute_fn=compute,
                reader_chapter=reader_chapter,
                query_params={
                    "from": from_chapter,
                    "to": actual_to,
                    "lim": limit,
                    "off": offset,
                },
            )
        return compute()

    def get_character_read_model(
        self,
        series_id: uuid.UUID,
        character_id: str,
        reader_chapter: int,
    ) -> CharacterReadModel:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_eid = EntityId(series_id)
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        try:
            char_eid = EntityId(uuid.UUID(character_id))
        except ValueError:
            char_eid = EntityId(character_id)

        character = self.character_repo.get(char_eid)
        if not character or (
            character.series_id and str(character.series_id.value) != str(series_id)
        ):
            raise CharacterNotFound(
                f"Character {character_id} not found in series {series_id}"
            )

        def compute() -> CharacterReadModel:
            chapter_val = ChapterNumber(reader_chapter)
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )
            world_state = self.world_state_builder.build(
                series_eid, envelopes, chapter_val
            )

            arc = self.narrative_engine.derive_character_arc(
                str(series_id),
                str(character.id.value),
                reader_chapter,
                envelopes,
                world_state,
            )

            char_state = world_state.characters.get(character.id)
            if not char_state:
                char_state = world_state.characters.get(str(character.id.value))

            status = (
                "alive"
                if (char_state and char_state.alive)
                else ("dead" if char_state else "unintroduced")
            )
            rank = char_state.rank if char_state else None
            fac_id = (
                str(char_state.faction_id)
                if (char_state and char_state.faction_id)
                else None
            )
            skills = (
                sorted(list(str(s) for s in char_state.unlocked_skills))
                if char_state
                else []
            )

            rel_count = sum(
                1
                for (s, t), r in world_state.relationships.items()
                if (
                    str(s) == str(character.id.value)
                    or str(t) == str(character.id.value)
                )
                and r.active
            )

            current_phase_title = arc.phases[-1].title if arc.phases else None

            temporal_ctx = TemporalContextReadModel(
                series_id=str(series_id),
                reader_chapter=reader_chapter,
                min_visible_chapter=1,
                max_visible_chapter=reader_chapter,
                future_information_excluded=True,
            )

            return CharacterReadModel(
                character_id=str(character.id.value),
                series_id=str(series_id),
                name=character.name,
                temporal_context=temporal_ctx,
                status=status,
                rank=rank,
                faction_id=fac_id,
                unlocked_skills=skills,
                active_relationships_count=rel_count,
                total_milestones_reached=len(arc.milestones),
                total_turning_points_passed=len(arc.turning_points),
                current_phase_title=current_phase_title,
                milestones=[_map_milestone_dto(m) for m in arc.milestones],
                turning_points=[
                    _map_turning_point_dto(tp) for tp in arc.turning_points
                ],
                phases=[_map_phase_dto(p) for p in arc.phases],
            )

        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource=f"read_model:character:{character.id.value}",
                compute_fn=compute,
                reader_chapter=reader_chapter,
            )
        return compute()

    def get_generic_graph(
        self,
        series_id: uuid.UUID,
        reader_chapter: int,
        graph_type: str = "causal",
    ) -> GenericGraphReadModel:
        """Returns a universal graph projection (nodes + edges) for frontend visualizers."""
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_eid = EntityId(series_id)
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        def compute() -> GenericGraphReadModel:
            chapter_val = ChapterNumber(reader_chapter)
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )
            world_state = self.world_state_builder.build(
                series_eid, envelopes, chapter_val
            )

            nodes: list[UniversalGraphNode] = []
            edges: list[UniversalGraphEdge] = []

            if graph_type == "relationship":
                chars = self.character_repo.get_all_by_series(series_eid)
                for c in chars:
                    nodes.append(
                        UniversalGraphNode(
                            id=str(c.id.value),
                            node_type="CHARACTER",
                            label=c.name,
                            chapter=reader_chapter,
                        )
                    )
                for (s, t), r in world_state.relationships.items():
                    if r.active:
                        edges.append(
                            UniversalGraphEdge(
                                edge_id=f"rel:{s}:{t}",
                                source_id=str(s),
                                target_id=str(t),
                                edge_type="RELATIONSHIP",
                                label=r.relationship_type.value
                                if hasattr(r.relationship_type, "value")
                                else str(r.relationship_type),
                                chapter=reader_chapter,
                            )
                        )
            else:
                # Causal graph
                causal_graph = self.causal_service.build_causal_graph(
                    str(series_id), envelopes, reader_chapter=reader_chapter
                )
                all_rels = causal_graph.get_all_relations()

                seen_nodes: set[str] = set()
                for r in all_rels:
                    if r.source_event_id not in seen_nodes:
                        seen_nodes.add(r.source_event_id)
                        nodes.append(
                            UniversalGraphNode(
                                id=r.source_event_id,
                                node_type="EVENT",
                                label=f"Event {r.source_event_id}",
                                chapter=r.source_chapter,
                            )
                        )
                    if r.target_event_id not in seen_nodes:
                        seen_nodes.add(r.target_event_id)
                        nodes.append(
                            UniversalGraphNode(
                                id=r.target_event_id,
                                node_type="EVENT",
                                label=f"Event {r.target_event_id}",
                                chapter=r.target_chapter,
                            )
                        )

                    edges.append(
                        UniversalGraphEdge(
                            edge_id=r.relation_id,
                            source_id=r.source_event_id,
                            target_id=r.target_event_id,
                            edge_type=r.relation_type.value,
                            label=r.relation_type.value,
                            chapter=r.target_chapter,
                            weight=r.impact_score,
                            evidence_summary=r.evidence.explanation_code
                            if r.evidence
                            else None,
                        )
                    )

            nodes.sort(key=lambda n: (n.chapter or 0, n.id))
            edges.sort(
                key=lambda e: (e.chapter or 0, e.source_id, e.target_id, e.edge_id)
            )

            temporal_ctx = TemporalContextReadModel(
                series_id=str(series_id),
                reader_chapter=reader_chapter,
                min_visible_chapter=1,
                max_visible_chapter=reader_chapter,
                future_information_excluded=True,
            )

            return GenericGraphReadModel(
                temporal_context=temporal_ctx,
                nodes=nodes,
                edges=edges,
            )

        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource=f"read_model:graph:{graph_type}",
                compute_fn=compute,
                reader_chapter=reader_chapter,
            )
        return compute()
