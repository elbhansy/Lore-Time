from packages.domain.provenance.lineage_dto import CanonicalEventLineageDTO
from packages.domain.provenance.provenance_reader import CanonicalEventProvenanceReader


class GetEventLineageUseCase:
    def __init__(self, reader: CanonicalEventProvenanceReader):
        self.reader = reader

    def execute(self, event_id: str) -> CanonicalEventLineageDTO | None:
        # Authorization and Security checks would go here.
        # Ensure the user has permission to view provenance for this event.
        return self.reader.get_event_lineage(event_id)
