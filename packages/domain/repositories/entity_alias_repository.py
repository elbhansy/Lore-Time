from abc import ABC, abstractmethod

from packages.domain.ingestion.entity_resolution import EntityAlias


class EntityAliasRepository(ABC):
    @abstractmethod
    def get_by_normalized_alias(
        self, series_id: str, entity_type: str, normalized_alias: str
    ) -> list[EntityAlias]:
        """
        Retrieves all active aliases matching the normalized string.
        Should return a list because the same normalized alias could theoretically map
        to multiple entities (which constitutes an AMBIGUOUS state).
        """
        pass

    @abstractmethod
    def save(self, alias: EntityAlias) -> None:
        pass

    @abstractmethod
    def deactivate(self, alias_id: str) -> None:
        pass
