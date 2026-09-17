from datetime import datetime

from apps.api.app.application.provenance.get_event_lineage_use_case import (
    GetEventLineageUseCase,
)
from packages.domain.provenance.lineage_dto import (
    CanonicalEventAuditDTO,
    CanonicalEventLineageDTO,
    ExtractedFactAuditDTO,
    ProvenanceAuditDTO,
    PublicationAuditDTO,
    ReviewItemAuditDTO,
)
from packages.domain.provenance.provenance_reader import CanonicalEventProvenanceReader


class MockProvenanceReader(CanonicalEventProvenanceReader):
    def __init__(self):
        # We simulate the db state here
        self.events = {}

    def get_event_lineage(self, event_id: str) -> CanonicalEventLineageDTO:
        if event_id not in self.events:
            return None
        return self.events[event_id]


def test_full_lineage_retrieval_and_multiple_attempts():
    reader = MockProvenanceReader()
    use_case = GetEventLineageUseCase(reader)

    # Simulate DB data for event_1
    publications = [
        PublicationAuditDTO(
            "pub_1",
            "FAILED",
            datetime(2026, 1, 1, 10, 0),
            "actor_1",
            "Validation error",
        ),
        PublicationAuditDTO(
            "pub_2", "FAILED", datetime(2026, 1, 1, 10, 5), "actor_1", "Network timeout"
        ),
        PublicationAuditDTO(
            "pub_3", "PUBLISHED", datetime(2026, 1, 1, 10, 10), "actor_1", None
        ),
    ]

    reader.events["event_1"] = CanonicalEventLineageDTO(
        event=CanonicalEventAuditDTO(
            "event_1", "s1", "c1", "RANK_UP", datetime(2026, 1, 1, 10, 10)
        ),
        review_item=ReviewItemAuditDTO(
            "rev_1", "PUBLISHED", "reviewer_1", datetime(2026, 1, 1, 9, 50)
        ),
        publications=publications,  # All 3 attempts
        extracted_fact=ExtractedFactAuditDTO("RANK_UP", "Dokja", None, {"rank": "A"}),
        provenance=ProvenanceAuditDTO("available", "source_1", "p42", 0.99, None),
    )

    lineage = use_case.execute("event_1")

    assert lineage is not None
    assert lineage.event.id == "event_1"
    assert len(lineage.publications) == 3
    assert lineage.publications[0].status == "FAILED"
    assert lineage.publications[-1].status == "PUBLISHED"
    assert lineage.provenance.status == "available"


def test_missing_provenance_degradation():
    reader = MockProvenanceReader()
    use_case = GetEventLineageUseCase(reader)

    # Event where provenance metadata was corrupted/lost in the DB
    reader.events["event_no_prov"] = CanonicalEventLineageDTO(
        event=CanonicalEventAuditDTO(
            "event_no_prov", "s1", "c1", "RANK_UP", datetime.now()
        ),
        review_item=ReviewItemAuditDTO(
            "rev_2", "PUBLISHED", "reviewer_1", datetime.now()
        ),
        publications=[
            PublicationAuditDTO("pub_x", "PUBLISHED", datetime.now(), None, None)
        ],
        extracted_fact=ExtractedFactAuditDTO("RANK_UP", "Dokja", None, {}),
        provenance=ProvenanceAuditDTO(
            "unavailable", None, None, None, "metadata_corrupted"
        ),
    )

    lineage = use_case.execute("event_no_prov")
    assert lineage.provenance.status == "unavailable"
    assert lineage.provenance.reason == "metadata_corrupted"
