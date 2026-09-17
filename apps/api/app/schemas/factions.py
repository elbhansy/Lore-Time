from pydantic import BaseModel


class FactionExplorerItemDTO(BaseModel):
    id: str
    name: str
    member_count: int
    introduced_chapter: int


class FactionProfileDTO(BaseModel):
    id: str
    name: str
    description: str | None = None
    introduced_chapter: int
    member_count: int
    leader_id: str | None = None
    leader_name: str | None = None
    active_relationships_count: int


class FactionMemberDTO(BaseModel):
    character_id: str
    character_name: str
    active: bool
    joined_at: int
    left_at: int | None = None


class FactionLeadershipDTO(BaseModel):
    leader_id: str
    leader_name: str
    active: bool
    started_at: int
    ended_at: int | None = None
