from packages.domain.ingestion.alias_normalizer import AliasNormalizer
from packages.domain.ingestion.entity_resolution import EntityAlias, ResolutionStatus
from packages.domain.services.entity_resolver_service import EntityResolverService


def test_alias_normalizer():
    assert AliasNormalizer.normalize("Kim Dokja") == "kim dokja"
    assert AliasNormalizer.normalize("  Kim   Dokja  ") == "kim dokja"
    assert AliasNormalizer.normalize("Kim Dok-Ja") == "kim dok ja"
    assert AliasNormalizer.normalize("“Dokja”") == "dokja"
    assert AliasNormalizer.normalize("") == ""
    assert AliasNormalizer.normalize(None) == ""


class MockEntityAliasRepo:
    def __init__(self):
        self.aliases = []

    def get_by_normalized_alias(self, series_id, entity_type, normalized_alias):
        return [
            a
            for a in self.aliases
            if a.series_id == series_id
            and a.entity_type == entity_type
            and a.normalized_alias == normalized_alias
            and a.active == True
        ]


def test_entity_resolver_unresolved():
    repo = MockEntityAliasRepo()
    service = EntityResolverService(repo)

    result = service.resolve("s1", "CHAR", "Unknown")
    assert result.status == ResolutionStatus.UNRESOLVED
    assert result.matched_alias == "unknown"
    assert result.entity_id is None


def test_entity_resolver_resolved():
    repo = MockEntityAliasRepo()
    repo.aliases.append(
        EntityAlias(
            id="1",
            series_id="s1",
            entity_id="e1",
            entity_type="CHAR",
            alias="Dokja",
            normalized_alias="dokja",
        )
    )

    service = EntityResolverService(repo)

    # "  Dok-ja " normalizes to "dok ja"
    # But the alias in the DB is "dokja" so it shouldn't match.
    result = service.resolve("s1", "CHAR", "  Dok-ja ")
    assert result.status == ResolutionStatus.UNRESOLVED
    assert result.matched_alias == "dok ja"

    # Test proper match with "Dokja" which normalizes to "dokja"
    result2 = service.resolve("s1", "CHAR", "dokja")
    assert result2.status == ResolutionStatus.RESOLVED
    assert result2.entity_id == "e1"


def test_entity_resolver_ambiguous():
    repo = MockEntityAliasRepo()
    repo.aliases.append(
        EntityAlias(
            id="1",
            series_id="s1",
            entity_id="e1",
            entity_type="CHAR",
            alias="Apollo",
            normalized_alias="apollo",
        )
    )
    repo.aliases.append(
        EntityAlias(
            id="2",
            series_id="s1",
            entity_id="e2",
            entity_type="CHAR",
            alias="Apollo",
            normalized_alias="apollo",
        )
    )

    service = EntityResolverService(repo)
    result = service.resolve("s1", "CHAR", "Apollo")

    assert result.status == ResolutionStatus.AMBIGUOUS
    assert result.entity_id is None
    assert result.matched_alias == "apollo"


def test_entity_resolver_ambiguous_cross_type():
    # If the alias is identical but the types are different, it is NOT ambiguous for a specific query
    repo = MockEntityAliasRepo()
    repo.aliases.append(
        EntityAlias(
            id="1",
            series_id="s1",
            entity_id="char_e1",
            entity_type="CHAR",
            alias="Apollo",
            normalized_alias="apollo",
        )
    )
    repo.aliases.append(
        EntityAlias(
            id="2",
            series_id="s1",
            entity_id="fac_e1",
            entity_type="FACTION",
            alias="Apollo",
            normalized_alias="apollo",
        )
    )

    service = EntityResolverService(repo)
    result = service.resolve("s1", "CHAR", "Apollo")

    # Resolves cleanly to the character
    assert result.status == ResolutionStatus.RESOLVED
    assert result.entity_id == "char_e1"
