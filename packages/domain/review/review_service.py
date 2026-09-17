from packages.domain.review.review_status import ReviewDecision, ReviewStatus


class ReviewDomainError(Exception):
    pass


class ReviewService:
    @staticmethod
    def apply_decision(
        current_status: ReviewStatus, decision: ReviewDecision
    ) -> ReviewStatus:
        if decision == ReviewDecision.APPROVE:
            if current_status == ReviewStatus.CONFLICT:
                raise ReviewDomainError(
                    "Cannot directly APPROVE an item in CONFLICT state. It must be CORRECTED first."
                )
            return ReviewStatus.APPROVED

        elif decision == ReviewDecision.REJECT:
            return ReviewStatus.REJECTED

        elif decision == ReviewDecision.CORRECT:
            if current_status == ReviewStatus.CONFLICT:
                # Correction resolves the conflict back to PENDING for re-evaluation
                return ReviewStatus.PENDING
            return ReviewStatus.NEEDS_CORRECTION

        raise ReviewDomainError(f"Unknown decision: {decision}")
