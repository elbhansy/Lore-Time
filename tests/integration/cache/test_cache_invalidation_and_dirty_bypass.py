"""Phase 4.8 Integration Tests: Cache Invalidation, Publication Consistency, and Dirty Namespace Bypass."""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.config import get_settings
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.review.review_item_model import ReviewItemModel
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture
def clean_cache():
    service = CacheService()
    reset_cache_service_for_testing(service)
    yield service
    service.clear()
    reset_cache_service_for_testing(None)


def test_publication_invalidates_cache_and_refreshes_world_state(clean_cache):
    """Verify:
    1. Query WorldState at chapter N -> Populates cache.
    2. Publish new canonical event for chapter N.
    3. Post-commit targeted cache invalidation occurs.
    4. Next query observes new canonical event in WorldState.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
        sid = uuid.UUID(series_id_str)

        # Get first chapter id
        chapter = session.query(ChapterModel).filter_by(series_id=sid, number=3).first()

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())
        ws_uc = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )

        # 1. Warm cache
        ws_initial = ws_uc.execute(sid, reader_chapter=3)
        initial_chars = len(ws_initial.characters)

        # Cache must have entries now
        assert clean_cache.stats()["entries"] >= 1

        # 2. Prepare review item for publication introducing a new character at chapter 3
        pub_repo = SQLAlchemyPublicationRepository(session)
        publish_uc = PublishReviewItemUseCase(pub_repo, cache_service=clean_cache)

        new_char_id = str(uuid.uuid4())
        fact = RawExtractedFact(
            type=FactType.CHARACTER_INTRODUCED,
            subject_raw="New Hero",
            target_raw=None,
            payload={
                "subject_id": new_char_id,
                "name": "New Hero",
                "character_id": new_char_id,
            },
            extraction_confidence=1.0,
            evidence=RawFactEvidence(location="ch3 p1"),
        )
        prov = Provenance(
            source_id="src1",
            evidence=Evidence(chapter_id=str(chapter.id), location="ch3 p1"),
            confidence=Confidence(1.0, 1.0, 1.0, 1.0),
            captured_at=datetime.now(),
        )
        rev_uuid = uuid.uuid4()
        session.add(
            ReviewItemModel(
                id=rev_uuid,
                series_id=sid,
                chapter_id=chapter.id,
                fact_type=fact.type.value,
                fact_payload=fact.payload,
                provenance_data=prov.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        session.commit()

        review_item = ReviewItem(
            id=str(rev_uuid),
            series_id=series_id_str,
            chapter_id=str(chapter.id),
            fact=fact,
            provenance=prov,
            status=ReviewStatus.APPROVED,
        )

        # Execute publication
        publish_uc.execute(review_item)

        # 3. Verify Cache Invalidation occurred for this series
        # The cache prefix for this series should have been invalidated
        ws_updated = ws_uc.execute(sid, reader_chapter=3)

        # The new character must be present in the newly computed world state
        assert any(str(c.value) == new_char_id for c in ws_updated.characters.keys())
        assert len(ws_updated.characters) == initial_chars + 1

    finally:
        session.close()
        engine.dispose()


def test_invalidation_failure_safety_marks_dirty_and_bypasses(clean_cache):
    """Verify:
    If cache invalidation throws an exception after successful DB commit:
    1. Transaction remains COMMITTED in PostgreSQL.
    2. Namespace is marked DIRTY.
    3. Subsequent reads bypass cache to PostgreSQL directly (zero stale reads).
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        series_id_str = seed_test_series(session, num_chapters=4, events_per_chapter=2)
        sid = uuid.UUID(series_id_str)
        chapter = session.query(ChapterModel).filter_by(series_id=sid, number=2).first()

        # Pre-seed cache
        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())
        ws_uc = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )

        ws_stale = ws_uc.execute(sid, reader_chapter=2)
        assert clean_cache.stats()["entries"] >= 1

        # Simulate cache backend throwing error on delete_prefix
        real_delete_prefix = clean_cache._backend.delete_prefix

        def broken_delete_prefix(prefix: str):
            raise RuntimeError("Simulated cache delete failure")

        clean_cache._backend.delete_prefix = broken_delete_prefix

        # Execute publication
        pub_repo = SQLAlchemyPublicationRepository(session)
        publish_uc = PublishReviewItemUseCase(pub_repo, cache_service=clean_cache)

        new_char_id = str(uuid.uuid4())
        fact = RawExtractedFact(
            type=FactType.CHARACTER_INTRODUCED,
            subject_raw="Bypass Hero",
            target_raw=None,
            payload={
                "subject_id": new_char_id,
                "name": "Bypass Hero",
                "character_id": new_char_id,
            },
            extraction_confidence=1.0,
            evidence=RawFactEvidence(location="ch2 p1"),
        )
        prov = Provenance(
            source_id="src1",
            evidence=Evidence(chapter_id=str(chapter.id), location="ch2 p1"),
            confidence=Confidence(1.0, 1.0, 1.0, 1.0),
            captured_at=datetime.now(),
        )
        rev_uuid = uuid.uuid4()
        session.add(
            ReviewItemModel(
                id=rev_uuid,
                series_id=sid,
                chapter_id=chapter.id,
                fact_type=fact.type.value,
                fact_payload=fact.payload,
                provenance_data=prov.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        session.commit()

        review_item = ReviewItem(
            id=str(rev_uuid),
            series_id=series_id_str,
            chapter_id=str(chapter.id),
            fact=fact,
            provenance=prov,
            status=ReviewStatus.APPROVED,
        )

        # Invalidation will fail, but publication MUST succeed and namespace must become DIRTY
        publish_uc.execute(review_item)
        assert review_item.status == ReviewStatus.PUBLISHED

        # Invariant: series namespace marked DIRTY
        assert clean_cache._backend.is_dirty(series_id_str)

        # Subsequent read MUST bypass cache and fetch directly from DB
        ws_fresh = ws_uc.execute(sid, reader_chapter=2)
        assert any(str(c.value) == new_char_id for c in ws_fresh.characters.keys())

    finally:
        session.close()
        engine.dispose()
