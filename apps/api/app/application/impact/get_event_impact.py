import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.impact.impact_result import ImpactAnalysisResult
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.services.event_impact_analyzer import EventImpactAnalyzer
from packages.domain.services.event_ordering import sort_events
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import EntityNotFound, InvalidChapter


class GetEventImpactUseCase:
    def __init__(
        self,
        event_repo: EventRepository,
        get_world_state_uc: GetWorldStateUseCase,
        analyzer: EventImpactAnalyzer,
    ):
        self.event_repo = event_repo
        self.get_world_state_uc = get_world_state_uc
        self.analyzer = analyzer

    def execute(
        self, series_id: uuid.UUID, event_id: uuid.UUID, reader_chapter: int
    ) -> ImpactAnalysisResult:
        if reader_chapter < 1:
            raise InvalidChapter("reader_chapter must be positive")

        series_eid = EntityId(series_id)
        event_eid = EntityId(event_id)

        # We need to find the event and its envelope to know its chapter
        envelopes = self.event_repo.get_all_by_series(series_eid)
        target_env = next((e for e in envelopes if e.event.id == event_eid), None)

        if not target_env:
            raise EntityNotFound(f"Event {event_id} not found in series {series_id}")

        event_chapter = target_env.chapter_number.value

        # Spoiler Firewall
        if event_chapter > reader_chapter:
            raise InvalidChapter(
                f"Cannot analyze event at chapter {event_chapter} because it exceeds reader_chapter {reader_chapter}"
            )

        # Reconstruct WorldState BEFORE the event
        # To do this safely, we get all envelopes strictly before this event, or we can just reconstruct at event_chapter - 1,
        # BUT there might be multiple events in the same chapter!
        # The correct way: reconstruct state by replaying envelopes up to this event, excluding this event.

        # 1. Filter out future chapters completely
        valid_envs = [e for e in envelopes if e.chapter_number.value <= event_chapter]
        valid_envs = sort_events(valid_envs)

        # 2. Find the index of our target event
        target_idx = -1
        for i, e in enumerate(valid_envs):
            if e.event.id == event_eid:
                target_idx = i
                break

        # 3. Get all envelopes BEFORE this event
        before_envs = valid_envs[:target_idx]

        # 4. Build WorldState manually using builder
        # We need the builder from world_state_uc
        builder = self.get_world_state_uc.builder
        state_before = builder.build(
            series_eid, before_envs, ChapterNumber(event_chapter)
        )

        # 5. Analyze
        result = self.analyzer.analyze(target_env.event, state_before)
        return result
