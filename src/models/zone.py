from enum import Enum
from dataclasses import dataclass
from typing import Optional


class InvalidZoneTypeError(ValueError):
    pass


class InaccessibleZoneError(Exception):
    pass


class ZoneType(Enum):
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    @classmethod
    def from_string(cls, value: str) -> ZoneType:
        for zone in ZoneType:
            if zone.value == value:
                return zone
        raise InvalidZoneTypeError(f"'{value}' isnt a valid zone")

    def movement_cost(self) -> int:
        if self == ZoneType.BLOCKED:
            raise InaccessibleZoneError("zona blocked não tem custo — é inválida")
        elif self == ZoneType.RESTRICTED:
            return 2
        else:
            return 1

    def is_accessible(self) -> bool:
        return self != ZoneType.BLOCKED


@dataclass
class Zone:
    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int = 1
    color: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("zone name cant be empty")
        if self.max_drones < 1:
            raise ValueError("max_drones needs to be an integer and positive")
        if "-" in self.name or " " in self.name:
            raise ValueError(f"invalid '{self.name}' name: cant have '-' or spaces")
    
    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name