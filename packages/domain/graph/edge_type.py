from enum import Enum


class EdgeType(str, Enum):
    # Relationships
    ALLY = "ALLY"
    ENEMY = "ENEMY"
    FRIEND = "FRIEND"
    RIVAL = "RIVAL"
    FAMILY = "FAMILY"
    MASTER = "MASTER"
    DISCIPLE = "DISCIPLE"

    # Organization
    MEMBER_OF = "MEMBER_OF"
    LEADS = "LEADS"

    # Power
    USES_POWER_SYSTEM = "USES_POWER_SYSTEM"
    HAS_RANK = "HAS_RANK"
    BELONGS_TO = "BELONGS_TO"
    UNLOCKED_SKILL = "UNLOCKED_SKILL"
