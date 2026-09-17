"""PostgreSQL implementation of PublicationRepository.

Enforces publishing atomicity and idempotency.
"""

import logging
import uuid

logger = logging.getLogger("timeline.db")

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from infrastructure.database.models.canonical_entity import CanonicalEntityModel
from infrastructure.database.models.canonical_relationship import (
    CanonicalRelationshipModel,
)
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.publication_record import (
    PublicationRecordModel,
)
from infrastructure.database.models.review.review_item_model import (
    ReviewItemModel,
)
from packages.domain.publishing.publication_status import PublicationStatus
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


class SQLAlchemyPublicationRepository:
    """Repository managing canonical publishing atomicity and idempotency."""

    def __init__(self, session: Session):
        self.session = session

    def execute_in_transaction(self, review_item: ReviewItem, action):
        """Wraps action in an atomic transaction.

        Rolls back entirely on any exception, ensuring NO PARTIAL CANONICAL STATE.
        """
        try:
            action()
            self.session.commit()
            logger.info(
                "Publication database transaction committed for review item %s",
                review_item.id,
                extra={
                    "event": "database.transaction.commit",
                    "resource_type": "review_item",
                    "resource_id": str(review_item.id),
                    "outcome": "success",
                },
            )
        except Exception as exc:
            self.session.rollback()
            logger.error(
                "Publication database transaction rolled back for review item %s: %s",
                review_item.id,
                exc,
                extra={
                    "event": "database.transaction.rollback",
                    "resource_type": "review_item",
                    "resource_id": str(review_item.id),
                    "error_code": "TRANSACTION_ROLLBACK",
                    "outcome": "failure",
                },
            )
            raise

    def lock_review_item(self, item_id: str):
        """Acquires a row-level lock (SELECT FOR UPDATE) to serialize workers."""
        try:
            uuid_id = uuid.UUID(str(item_id))
        except ValueError:
            return None
        return (
            self.session.query(ReviewItemModel)
            .filter_by(id=uuid_id)
            .with_for_update()
            .first()
        )

    def save_event(self, event_data: dict) -> str:
        """Saves canonical event idempotently using ON CONFLICT DO NOTHING.

        Guarantees that concurrent workers produce exactly ONE canonical event.
        """
        fingerprint = event_data.get("publication_fingerprint")

        # 1. First check if already exists by fingerprint
        if fingerprint:
            existing = (
                self.session.query(EventModel)
                .filter_by(publication_fingerprint=fingerprint)
                .first()
            )
            if existing:
                return str(existing.id)

        # 2. Insert with ON CONFLICT DO NOTHING for concurrency race protection
        event_id = uuid.uuid4()
        target_id_val = (
            uuid.UUID(str(event_data["target_id"]))
            if event_data.get("target_id")
            else None
        )
        stmt = (
            insert(EventModel)
            .values(
                id=event_id,
                series_id=uuid.UUID(str(event_data["series_id"])),
                chapter_id=uuid.UUID(str(event_data["chapter_id"])),
                sequence=event_data.get("sequence", 0),
                type=event_data["type"],
                subject_type=event_data.get("subject_type", "CHARACTER"),
                subject_id=uuid.UUID(str(event_data["subject_id"])),
                target_type=event_data.get("target_type"),
                target_id=target_id_val,
                previous_state=event_data.get("previous_state") or {},
                new_state=event_data.get("new_state") or {},
                metadata_=event_data.get("metadata") or {},
                publication_fingerprint=fingerprint,
            )
            .on_conflict_do_nothing(index_elements=["publication_fingerprint"])
        )

        self.session.execute(stmt)
        self.session.flush()

        # 3. Retrieve actual row (either the one we inserted or race winner)
        if fingerprint:
            actual = (
                self.session.query(EventModel)
                .filter_by(publication_fingerprint=fingerprint)
                .first()
            )
            if actual:
                return str(actual.id)

        return str(event_id)

    def save_publication_record(self, record_data: dict):
        event_id_val = (
            uuid.UUID(str(record_data["event_id"]))
            if record_data.get("event_id")
            else None
        )
        record = PublicationRecordModel(
            id=uuid.uuid4(),
            review_item_id=uuid.UUID(str(record_data["review_item_id"])),
            event_id=event_id_val,
            status=record_data.get("status", PublicationStatus.PUBLISHED.value),
            error_message=record_data.get("error_message"),
            actor_id=record_data.get("actor_id"),
        )
        self.session.add(record)
        self.session.flush()

    def update_review_status(self, review_item: ReviewItem, status: ReviewStatus):
        try:
            uuid_id = uuid.UUID(str(review_item.id))
            item_model = (
                self.session.query(ReviewItemModel).filter_by(id=uuid_id).first()
            )
            if item_model:
                status_val = status.value if hasattr(status, "value") else str(status)
                item_model.status = status_val
                self.session.flush()
        except ValueError:
            pass
        review_item.status = status

    def ensure_entity_exists(
        self, entity_id: str, series_id: str, type: str, name: str
    ):
        stmt = (
            insert(CanonicalEntityModel)
            .values(
                id=str(entity_id),
                series_id=str(series_id),
                type=str(type),
                name=str(name),
                metadata_={},
            )
            .on_conflict_do_nothing(index_elements=["series_id", "id"])
        )
        self.session.execute(stmt)
        self.session.flush()

    def create_relationship(
        self,
        series_id: str,
        source_id: str,
        target_id: str,
        rel_type: str,
        event_id: str,
        sequence: int,
    ):
        rel = CanonicalRelationshipModel(
            id=uuid.uuid4(),
            series_id=str(series_id),
            source_entity_id=str(source_id),
            target_entity_id=str(target_id),
            type=str(rel_type),
            event_id=uuid.UUID(str(event_id)),
            sequence=sequence,
        )
        self.session.add(rel)
        self.session.flush()
