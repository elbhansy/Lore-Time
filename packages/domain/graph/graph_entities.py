from dataclasses import dataclass


@dataclass
class EntityMetadata:
    name: str
    introduced_chapter: int | None = None
    description: str | None = None
    parent_id: str | None = None
    system_id: str | None = None


@dataclass
class GraphEntities:
    characters: dict[str, EntityMetadata]
    factions: dict[str, EntityMetadata]
    power_systems: dict[str, EntityMetadata]
    ranks: dict[str, EntityMetadata]
    skills: dict[str, EntityMetadata]
