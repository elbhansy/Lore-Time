from abc import ABC, abstractmethod

from packages.domain.provenance.lineage_dto import CanonicalEventLineageDTO


class CanonicalEventProvenanceReader(ABC):
    @abstractmethod
    def get_event_lineage(self, event_id: str) -> CanonicalEventLineageDTO | None:
        """
        Retrieves the full audit lineage for a given canonical event ID.
        Returns None if the event does not exist.
        """
        pass
