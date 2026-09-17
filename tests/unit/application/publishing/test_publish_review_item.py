from datetime import datetime

import pytest

from apps.api.app.application.publishing.publish_review_item import (
    MockPublicationRepo,
    PublishReviewItemUseCase,
)
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.publishing.canonical_publisher import PublicationDomainError
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


def create_mock_review_item(status: ReviewStatus) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={"from_rank": "B", "to_rank": "A", "subject_id": "dokja_uuid"},
        extraction_confidence=0.9,
        evidence=RawFactEvidence(location="p1"),
    )
    prov = Provenance(
        source_id="s1",
        evidence=Evidence(chapter_id="c1", location="p1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    return ReviewItem(
        id="r1",
        series_id="s1",
        chapter_id="c1",
        fact=fact,
        provenance=prov,
        status=status,
    )


def test_governance_blocks_pending():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_review_item(ReviewStatus.PENDING)

    with pytest.raises(
        PublicationDomainError, match="Cannot publish ReviewItem in state: PENDING"
    ):
        use_case.execute(item)


def test_idempotent_publishing():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_review_item(ReviewStatus.APPROVED)

    # Publish 3 times
    use_case.execute(item)
    use_case.execute(item)
    use_case.execute(item)

    # Should result in exactly 1 event
    assert len(repo.events) == 1

    # Should result in 1 publication record since early return
    assert len(repo.records) == 1
    event_id = list(repo.events.keys())[0]
    for r in repo.records.values():
        assert r["event_id"] == event_id

    assert item.status == ReviewStatus.PUBLISHED


def test_transaction_integrity():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_review_item(ReviewStatus.APPROVED)

    # Trigger a mock DB failure during publication record insertion
    repo.should_fail_record = True

    with pytest.raises(RuntimeError, match="Transaction failed"):
        use_case.execute(item)

    # The transaction rolled back, so the ReviewItem should still be APPROVED
    # (In our mock we assert the status wasn't mutated to PUBLISHED)
    assert item.status == ReviewStatus.APPROVED
