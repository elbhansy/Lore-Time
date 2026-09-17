import pytest

from packages.domain.review.review_service import ReviewDomainError, ReviewService
from packages.domain.review.review_status import ReviewDecision, ReviewStatus


def test_review_service_approve_pending():
    status = ReviewService.apply_decision(ReviewStatus.PENDING, ReviewDecision.APPROVE)
    assert status == ReviewStatus.APPROVED


def test_review_service_reject_pending():
    status = ReviewService.apply_decision(ReviewStatus.PENDING, ReviewDecision.REJECT)
    assert status == ReviewStatus.REJECTED


def test_review_service_correct_pending():
    status = ReviewService.apply_decision(ReviewStatus.PENDING, ReviewDecision.CORRECT)
    assert status == ReviewStatus.NEEDS_CORRECTION


def test_review_service_approve_conflict_fails():
    with pytest.raises(
        ReviewDomainError, match="Cannot directly APPROVE an item in CONFLICT state"
    ):
        ReviewService.apply_decision(ReviewStatus.CONFLICT, ReviewDecision.APPROVE)


def test_review_service_correct_conflict():
    status = ReviewService.apply_decision(ReviewStatus.CONFLICT, ReviewDecision.CORRECT)
    assert status == ReviewStatus.PENDING  # Must be re-evaluated as PENDING
