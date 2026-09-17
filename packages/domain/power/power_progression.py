from dataclasses import dataclass, field

from packages.domain.power.rank_transition import RankTransition


@dataclass
class PowerProgression:
    character_id: str
    power_system_id: str
    current_rank: str | None
    transitions: list[RankTransition] = field(default_factory=list)
