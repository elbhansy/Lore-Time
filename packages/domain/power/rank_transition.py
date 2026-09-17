from dataclasses import dataclass


@dataclass
class RankTransition:
    character_id: str
    power_system_id: str
    from_rank_id: str | None
    to_rank_id: str
    chapter: int
    event_id: str
