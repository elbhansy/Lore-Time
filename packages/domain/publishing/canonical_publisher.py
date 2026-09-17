from packages.domain.publishing.publication_fingerprint import PublicationFingerprint
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


class PublicationDomainError(Exception):
    pass


class CanonicalPublisher:
    @staticmethod
    def prepare_event_data(review_item: ReviewItem) -> dict:
        """
        Validates the ReviewItem and prepares the canonical Event data mapping.
        Raises Domain Error if the item is not APPROVED.
        """
        if review_item.status != ReviewStatus.APPROVED:
            raise PublicationDomainError(
                f"Cannot publish ReviewItem in state: {review_item.status.value}"
            )

        # The EntityResolver (M2.0) would have populated subject_id and target_id in the ReviewItem's payload.
        # For safety, we expect the ReviewItem's fact payload to contain them, or the CanonicalPublisher to receive them.
        # Assuming payload contains the resolved IDs for the canonical event.
        payload = review_item.fact.payload
        subject_id = payload.get("subject_id", "")
        target_id = payload.get("target_id", None)

        if not subject_id:
            raise PublicationDomainError(
                "Cannot publish fact without a resolved subject_id"
            )

        fingerprint = PublicationFingerprint.generate(
            series_id=review_item.series_id,
            chapter_id=review_item.chapter_id,
            event_type=review_item.fact.type.value,
            subject_id=subject_id,
            target_id=target_id,
            payload=payload,
        )

        return {
            "series_id": review_item.series_id,
            "chapter_id": review_item.chapter_id,
            "sequence": payload.get("sequence", 0),
            "type": review_item.fact.type.value,
            "subject_id": subject_id,
            "target_id": target_id,
            "metadata": {**payload, "provenance": review_item.provenance.to_dict()},
            "publication_fingerprint": fingerprint,
        }
