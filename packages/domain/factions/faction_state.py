from dataclasses import dataclass, field


@dataclass
class FactionState:
    faction_id: str
    exists: bool = False
    metadata: dict = field(default_factory=dict)
