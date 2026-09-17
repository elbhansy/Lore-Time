from dataclasses import dataclass

from ..value_objects.entity_id import EntityId


@dataclass
class PowerState:
    power_system_id: EntityId
    # Future expansions go here
