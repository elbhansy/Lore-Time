from packages.domain.ingestion.alias_normalizer import AliasNormalizer
from packages.domain.ingestion.entity_resolution import (
    ResolutionResult,
    ResolutionStatus,
)
from packages.domain.repositories.entity_alias_repository import EntityAliasRepository


class EntityResolverService:
    def __init__(self, alias_repository: EntityAliasRepository):
        self.alias_repository = alias_repository

    def resolve(
        self, series_id: str, entity_type: str, raw_name: str
    ) -> ResolutionResult:
        normalized_alias = AliasNormalizer.normalize(raw_name)

        if not normalized_alias:
            return ResolutionResult(status=ResolutionStatus.UNRESOLVED)

        aliases = self.alias_repository.get_by_normalized_alias(
            series_id, entity_type, normalized_alias
        )

        if not aliases:
            return ResolutionResult(
                status=ResolutionStatus.UNRESOLVED, matched_alias=normalized_alias
            )

        # Get unique entity IDs that this alias points to
        unique_entity_ids = list(set(a.entity_id for a in aliases))

        if len(unique_entity_ids) > 1:
            # AMBIGUOUS: The same alias points to multiple distinct entities of the same type
            return ResolutionResult(
                status=ResolutionStatus.AMBIGUOUS, matched_alias=normalized_alias
            )

        # RESOLVED: Points to exactly one entity
        target_alias = aliases[0]
        return ResolutionResult(
            status=ResolutionStatus.RESOLVED,
            entity_id=target_alias.entity_id,
            confidence=target_alias.confidence,
            matched_alias=normalized_alias,
        )
