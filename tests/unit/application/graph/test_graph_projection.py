from datetime import datetime

import pytest

from apps.api.app.application.publishing.publish_review_item import (
    MockPublicationRepo,
    PublishReviewItemUseCase,
)
from packages.domain.extraction.extraction_result import (
    FactType,
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


def create_mock_rel_review_item(status: ReviewStatus) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.RELATIONSHIP_CHANGED,
        subject_raw="sub_1",
        target_raw="target_1",
        payload={"relation": "KNOWS", "subject_id": "sub_1", "target_id": "target_1"},
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
        id="rev_rel_1",
        series_id="s1",
        chapter_id="c1",
        fact=fact,
        provenance=prov,
        status=status,
        reviewer_id="reviewer_1",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


def test_missing_entity_auto_upsert_and_relationship_projection():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_rel_review_item(ReviewStatus.APPROVED)

    # 1. Execute publication
    use_case.execute(item)

    # 2. Verify graph projection auto-created the subject entity
    # Our mock event has subject_id="sub_1" and target_id="target_1"
    assert len(repo.entities) == 2
    assert "s1:sub_1" in repo.entities
    assert "s1:target_1" in repo.entities

    # 3. Verify relationships
    assert len(repo.relationships) == 1
    rel = repo.relationships[0]
    assert rel["source_id"] == "sub_1"
    assert rel["target_id"] == "target_1"


def test_curated_entity_preservation():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    # Pre-populate a curated entity
    repo.ensure_entity_exists("sub_1", "s1", "CHARACTER", "Alice")
    repo.entities["s1:sub_1"]["metadata"] = {"curated": True}

    item = create_mock_rel_review_item(ReviewStatus.APPROVED)
    use_case.execute(item)

    # Verify the curated entity wasn't overwritten by the generic projection logic
    # In our mock repo, ensure_entity_exists doesn't overwrite if it exists, matching the required domain rule.
    assert repo.entities["s1:sub_1"]["metadata"].get("curated") is True


def test_transaction_rollback_on_projection_failure():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_rel_review_item(ReviewStatus.APPROVED)

    # Sabotage the graph projector to throw an error
    def failing_project_event(*args):
        raise RuntimeError("DB Connection Lost during projection")

    use_case.graph_projector.project_event = failing_project_event

    with pytest.raises(RuntimeError, match="DB Connection Lost during projection"):
        use_case.execute(item)

    # Verify entire transaction rolled back
    assert len(repo.events) == 0
    assert len(repo.records) == 0
    assert item.status == ReviewStatus.APPROVED  # Should NOT be PUBLISHED


def test_repeated_publication_idempotency_for_graph():
    repo = MockPublicationRepo()
    use_case = PublishReviewItemUseCase(repo)

    item = create_mock_rel_review_item(ReviewStatus.APPROVED)

    # Publish multiple times
    use_case.execute(item)
    use_case.execute(item)
    use_case.execute(item)

    # Due to early return in idempotency logic of PublishReviewItemUseCase, it should only project once
    assert len(repo.relationships) == 1
    assert len(repo.entities) == 2
