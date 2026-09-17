import logging
import time

from packages.domain.publishing.canonical_publisher import (
    CanonicalPublisher,
    PublicationDomainError,
)
from packages.domain.publishing.publication_status import PublicationStatus
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus

logger = logging.getLogger("timeline.publisher")


class MockPublicationRepo:
    def __init__(self):
        self.events = {}
        self.records = {}
        self.should_fail_record = False
        self.locked_items = set()
        self.entities = {}
        self.relationships = []

    def execute_in_transaction(self, review_item, action):
        # Mocks a db transaction boundary
        backup_events = dict(self.events)
        backup_records = dict(self.records)
        backup_entities = dict(self.entities)
        backup_rels = list(self.relationships)
        try:
            action()
        except Exception:
            self.events = backup_events
            self.records = backup_records
            self.entities = backup_entities
            self.relationships = backup_rels
            raise

    def lock_review_item(self, item_id: str):
        pass

    def save_event(self, event_data: dict) -> str:
        # Idempotency check: Upsert or ignore on fingerprint
        fingerprint = event_data["publication_fingerprint"]

        # Check if already exists (simulate ON CONFLICT DO NOTHING)
        for e_id, e_data in self.events.items():
            if e_data["publication_fingerprint"] == fingerprint:
                return e_id  # return existing

        new_id = f"ev_{len(self.events) + 1}"
        self.events[new_id] = event_data
        return new_id

    def save_publication_record(self, record_data: dict):
        if self.should_fail_record:
            raise Exception("DB Failure: PublicationRecord INSERT failed")

        r_id = f"rec_{len(self.records) + 1}"
        self.records[r_id] = record_data

    def update_review_status(self, review_item: ReviewItem, status: str):
        review_item.status = status  # Just mutating the object for mock

    def ensure_entity_exists(
        self, entity_id: str, series_id: str, type: str, name: str
    ):
        key = f"{series_id}:{entity_id}"
        if key not in self.entities:
            self.entities[key] = {
                "id": entity_id,
                "series_id": series_id,
                "type": type,
                "name": name,
                "metadata": {},
            }

    def create_relationship(
        self, series_id, source_id, target_id, rel_type, event_id, sequence
    ):
        # In a real system, would handle uniqueness or idempotency based on (event_id, rel_type) etc.
        self.relationships.append(
            {
                "series_id": series_id,
                "source_id": source_id,
                "target_id": target_id,
                "type": rel_type,
                "event_id": event_id,
                "sequence": sequence,
            }
        )


from apps.api.app.application.graph.graph_projection_service import (
    GraphProjectionService,
)
from apps.api.app.core.cache import CacheService, get_cache_service


class PublishReviewItemUseCase:
    def __init__(self, repo, cache_service: CacheService | None = None):
        self.repo = repo
        self.graph_projector = GraphProjectionService(repo)
        self.cache_service = cache_service or get_cache_service()

    def execute(self, review_item: ReviewItem):
        # 0. Idempotency Check
        if review_item.status == ReviewStatus.PUBLISHED:
            logger.info(
                "Review item %s is already published (idempotent no-op)",
                review_item.id,
                extra={
                    "event": "review.publish.completed",
                    "resource_type": "review_item",
                    "resource_id": str(review_item.id),
                    "series_id": str(review_item.series_id),
                    "outcome": "success",
                },
            )
            return

        start_time = time.perf_counter()
        logger.info(
            "Starting publication for review item %s (series: %s)",
            review_item.id,
            review_item.series_id,
            extra={
                "event": "review.publish.started",
                "resource_type": "review_item",
                "resource_id": str(review_item.id),
                "series_id": str(review_item.series_id),
            },
        )

        # 1. Start Transaction
        def tx_action():
            # 2. Lock item and check current committed status inside transaction
            locked = self.repo.lock_review_item(review_item.id)
            if locked is not None:
                current_status = getattr(locked, "status", None)
                if current_status in (
                    ReviewStatus.PUBLISHED.value,
                    ReviewStatus.PUBLISHED,
                ):
                    review_item.status = ReviewStatus.PUBLISHED
                    logger.info(
                        "Review item %s was published concurrently by another worker",
                        review_item.id,
                        extra={
                            "event": "review.publish.conflict",
                            "resource_type": "review_item",
                            "resource_id": str(review_item.id),
                            "series_id": str(review_item.series_id),
                            "outcome": "success",
                        },
                    )
                    return

            # 3. Validate and Build Event
            event_data = CanonicalPublisher.prepare_event_data(review_item)

            # 4. Insert Event (Idempotent)
            event_id = self.repo.save_event(event_data)

            # 4.5 Atomic Graph Projection
            self.graph_projector.project_event(event_data, event_id)

            # 5. Create Publication Record
            self.repo.save_publication_record(
                {
                    "review_item_id": review_item.id,
                    "event_id": event_id,
                    "status": PublicationStatus.PUBLISHED.value,
                }
            )

            # 6. Mark ReviewItem Published
            self.repo.update_review_status(review_item, ReviewStatus.PUBLISHED)

        try:
            self.repo.execute_in_transaction(review_item, tx_action)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Publication succeeded for review item %s in %sms",
                review_item.id,
                duration_ms,
                extra={
                    "event": "review.publish.completed",
                    "resource_type": "review_item",
                    "resource_id": str(review_item.id),
                    "series_id": str(review_item.series_id),
                    "duration_ms": duration_ms,
                    "outcome": "success",
                },
            )
            # Post-Commit Correctness-First Cache Invalidation
            # If invalidation encounters an error, the namespace is marked DIRTY
            # and subsequent reads bypass the cache. Committed DB transaction is NOT rolled back.
            try:
                self.cache_service.invalidate_series(review_item.series_id)
            except Exception as inv_err:
                logger.critical(
                    "Post-commit cache invalidation failure for series %s: %s",
                    review_item.series_id,
                    inv_err,
                )
        except Exception as e:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            if isinstance(e, PublicationDomainError):
                logger.warning(
                    "Publication rejected for review item %s: %s",
                    review_item.id,
                    e,
                    extra={
                        "event": "review.publish.rejected",
                        "resource_type": "review_item",
                        "resource_id": str(review_item.id),
                        "series_id": str(review_item.series_id),
                        "duration_ms": duration_ms,
                        "error_code": "PUBLICATION_REJECTED",
                        "outcome": "rejected",
                    },
                )
                raise
            logger.error(
                "Publication transaction failed for review item %s: %s",
                review_item.id,
                e,
                extra={
                    "event": "review.publish.rollback",
                    "resource_type": "review_item",
                    "resource_id": str(review_item.id),
                    "series_id": str(review_item.series_id),
                    "duration_ms": duration_ms,
                    "error_code": "TRANSACTION_FAILURE",
                    "outcome": "failure",
                },
            )
            # In a real DB, the transaction rolls back here.
            raise RuntimeError(f"Transaction failed: {e}")
