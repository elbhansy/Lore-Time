"""Tests for Milestone 4.6.7: Publication Lifecycle Observability."""

import logging
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.review.review_item_model import (
    ReviewItemModel,
)
from infrastructure.database.models.series import SeriesModel
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.publishing.canonical_publisher import (
    PublicationDomainError,
)
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture
def pub_session_factory():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)


def test_publication_lifecycle_logging_success(pub_session_factory, caplog):
    """Verifies that publishing an approved review item emits review.publish.started

    and review.publish.completed, as well as database.transaction.commit.
    """
    caplog.set_level(logging.INFO)

    series_id = uuid.uuid4()
    chapter_id = uuid.uuid4()
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    init_session = pub_session_factory()
    s = SeriesModel(
        id=series_id,
        title="Obs Concurrency Series",
        slug=f"obs-{str(series_id)[:8]}",
        total_chapters=50,
    )
    c = ChapterModel(
        id=chapter_id,
        series_id=series_id,
        number=10,
        title="Obs Chapter 10",
    )
    init_session.add(s)
    init_session.add(c)
    init_session.commit()

    item_model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=series_id,
        chapter_id=chapter_id,
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={"from_rank": "C", "to_rank": "A", "subject_id": char_id},
        provenance_data={},
        status=ReviewStatus.APPROVED.value,
    )
    init_session.add(item_model)
    init_session.commit()
    init_session.close()

    worker_session = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(worker_session)
    use_case = PublishReviewItemUseCase(repo)

    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={
            "from_rank": "C",
            "to_rank": "A",
            "subject_id": char_id,
            "sequence": 1,
        },
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="webnovel_ch10",
        evidence=Evidence(chapter_id=str(chapter_id), location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    item = ReviewItem(
        id=item_id,
        series_id=str(series_id),
        chapter_id=str(chapter_id),
        fact=fact,
        provenance=prov,
        status=ReviewStatus.APPROVED,
    )

    use_case.execute(item)
    worker_session.close()

    started_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "review.publish.started"
    ]
    completed_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "review.publish.completed"
    ]
    db_commit_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "database.transaction.commit"
    ]

    assert len(started_events) >= 1
    assert len(completed_events) >= 1
    assert len(db_commit_events) >= 1
    assert completed_events[0].outcome == "success"


def test_publication_lifecycle_logging_rejected(pub_session_factory, caplog):
    """Verifies that attempting to publish a pending item logs review.publish.rejected."""
    caplog.set_level(logging.INFO)

    session = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(session)
    use_case = PublishReviewItemUseCase(repo)

    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw=None,
        payload={"to_rank": "A", "subject_id": str(uuid.uuid4())},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="src1",
        evidence=Evidence(chapter_id=str(uuid.uuid4()), location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    item = ReviewItem(
        id=str(uuid.uuid4()),
        series_id=str(uuid.uuid4()),
        chapter_id=str(uuid.uuid4()),
        fact=fact,
        provenance=prov,
        status=ReviewStatus.PENDING,
    )

    with pytest.raises(PublicationDomainError):
        use_case.execute(item)
    session.close()

    rejected_events = [
        r
        for r in caplog.records
        if getattr(r, "event", None) == "review.publish.rejected"
    ]
    assert len(rejected_events) >= 1
    assert rejected_events[0].outcome == "rejected"
