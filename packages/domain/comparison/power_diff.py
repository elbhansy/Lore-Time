from dataclasses import dataclass


@dataclass(frozen=True)
class PowerDiff:
    character_id: str
    before_rank: str | None
    after_rank: str | None
