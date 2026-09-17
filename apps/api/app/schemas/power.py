from typing import Any

from pydantic import BaseModel


class RankDTO(BaseModel):
    id: str
    name: str | None = None
    order: int | None = None


class RankTransitionDTO(BaseModel):
    from_rank_id: str | None = None
    from_rank_name: str | None = None
    to_rank_id: str
    to_rank_name: str | None = None
    chapter: int
    event_id: str
    breakthrough_status: str


class PowerProgressionDTO(BaseModel):
    character_id: str
    power_system_id: str
    current_rank: RankDTO | None = None
    transitions: list[RankTransitionDTO]


class RankDistributionItemDTO(BaseModel):
    rank_id: str
    rank_name: str
    order: int
    count: int


class PowerSystemDistributionDTO(BaseModel):
    power_system_id: str
    distribution: list[RankDistributionItemDTO]


class PowerComparisonDTO(BaseModel):
    character_a: dict[str, Any]
    character_b: dict[str, Any]
    result: str
