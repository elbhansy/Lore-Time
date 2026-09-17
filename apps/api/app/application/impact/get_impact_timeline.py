import uuid

from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from packages.domain.impact.impact_result import ImpactAnalysisResult
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.services.event_impact_analyzer import EventImpactAnalyzer
from packages.domain.services.event_ordering import sort_events
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import InvalidChapter


class GetImpactTimelineUseCase:
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
        self,
        series_id: uuid.UUID,
        from_chapter: int,
        to_chapter: int,
        reader_chapter: int,
    ) -> list[ImpactAnalysisResult]:
        if from_chapter < 1 or to_chapter < from_chapter:
            raise InvalidChapter("Invalid chapter bounds")
        if to_chapter > reader_chapter:
            raise InvalidChapter("to_chapter cannot exceed reader_chapter")

        series_eid = EntityId(series_id)
        envelopes = self.event_repo.get_all_by_series(series_eid)

        # Filter strictly up to to_chapter
        valid_envs = [e for e in envelopes if e.chapter_number.value <= to_chapter]
        valid_envs = sort_events(valid_envs)

        builder = self.get_world_state_uc.builder
        results = []

        # We build state iteratively to avoid rebuilding from scratch for every event
        current_state = builder.build(series_eid, [], ChapterNumber(0))  # Empty state

        for env in valid_envs:
            ch = env.chapter_number.value

            # If the event is within the window, analyze it
            if from_chapter <= ch <= to_chapter:
                result = self.analyzer.analyze(env.event, current_state)
                results.append(result)

            # Advance the state
            # Current state becomes the "before" state for the next event
            self.get_world_state_uc.builder.applier.apply(current_state, env)
            current_state.chapter = env.chapter_number

        return results
