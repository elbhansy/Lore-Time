from pydantic import BaseModel


class PowerSystemResponse(BaseModel):
    id: str
    series_id: str
    name: str
    slug: str
    description: str | None = None


class RankResponse(BaseModel):
    id: str
    power_system_id: str
    name: str
    slug: str
    order: int
    introduced_chapter: int
    description: str | None = None
    parent_rank_id: str | None = None
