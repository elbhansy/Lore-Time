from dataclasses import dataclass


@dataclass
class RankState:
    rank_id: str
    power_system_id: str
    available: bool
    introduced_at: int
