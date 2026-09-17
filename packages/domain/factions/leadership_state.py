from dataclasses import dataclass


@dataclass
class LeadershipState:
    faction_id: str
    leader_id: str
    active: bool
    started_at: int
    ended_at: int | None = None
