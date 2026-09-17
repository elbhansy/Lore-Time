from packages.domain.canonical.graph.canonical_entity import CanonicalEntity
from packages.domain.canonical.graph.canonical_relationship import CanonicalRelationship
from packages.domain.canonical.graph.graph_reader import (
    CanonicalGraphReader,
    GraphQuery,
)
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


class GetEntityUseCase:
    def __init__(self, reader: CanonicalGraphReader):
        self.reader = reader

    def execute(self, series_id: str, entity_id: str) -> CanonicalEntity | None:
        return self.reader.get_entity(series_id, entity_id)


class GetEntityRelationshipsUseCase:
    def __init__(self, reader: CanonicalGraphReader):
        self.reader = reader

    def execute(self, query: GraphQuery) -> PaginatedResponse[CanonicalRelationship]:
        return self.reader.get_entity_relationships(query)
