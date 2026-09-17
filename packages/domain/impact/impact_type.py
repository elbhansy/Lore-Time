from enum import Enum


class ImpactType(str, Enum):
    DIRECT = "DIRECT"
    DERIVED = "DERIVED"
    CORRELATED = "CORRELATED"
