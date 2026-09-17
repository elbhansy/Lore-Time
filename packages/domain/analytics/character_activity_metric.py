from dataclasses import dataclass


@dataclass(frozen=True)
class CharacterActivityMetric:
    entity_id: str
    # Events where the entity appears as subject OR target.
    event_count: int
    subject_count: int
    target_count: int
    # Canonical relationship rows touching this entity (either side),
    # from the same source CanonicalGraphReader reads.
    relationship_count: int
    chapters_present: int
    first_seen_chapter: int | None  # None when zero events in scope
    last_seen_chapter: int | None
