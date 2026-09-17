from dataclasses import dataclass


@dataclass
class MembershipState:
    character_id: str
    faction_id: str
    active: bool
    joined_at: int
    left_at: int | None = None
