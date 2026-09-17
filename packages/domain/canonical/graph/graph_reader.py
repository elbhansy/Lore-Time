from abc import ABC, abstractmethod
from dataclasses import dataclass

from packages.domain.canonical.graph.canonical_entity import CanonicalEntity
from packages.domain.canonical.graph.canonical_relationship import CanonicalRelationship
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


@dataclass
class GraphQuery:
    series_id: str
    entity_id: str
    page: int = 1
    limit: int = 50


class CanonicalGraphReader(ABC):
    @abstractmethod
    def get_entity(self, series_id: str, entity_id: str) -> CanonicalEntity | None:
        pass

    @abstractmethod
    def get_entity_relationships(
        self, query: GraphQuery
    ) -> PaginatedResponse[CanonicalRelationship]:
        pass
