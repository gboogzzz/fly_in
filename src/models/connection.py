from dataclasses import dataclass
from .zone import Zone


class InvalidConnectionError(ValueError):
    pass


@dataclass
class Connection:
    zone1: Zone
    zone2: Zone
    max_link_capacity: int = 1

    def __post_init__(self) -> None:
        if self.zone1 == self.zone2:
            raise InvalidConnectionError("The zone cant connect to itself")
        if self.max_link_capacity < 1:
            raise InvalidConnectionError("max link capacity needs \
            to be positive")

    def __hash__(self) -> int:
        return hash(frozenset({self.zone1.name, self.zone2.name}))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Connection):
            return NotImplemented
        return (
            {self.zone1.name, self.zone2.name} ==
            {other.zone1.name, other.zone2.name}
        )

    def involves(self, zone: Zone) -> bool:
        return zone == self.zone1 or zone == self.zone2
