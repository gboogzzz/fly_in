from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from .zone import Zone


class DroneState(Enum):
    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


@dataclass
class Drone:
    drone_id: int
    current_zone: Zone
    state: DroneState = DroneState.WAITING
    path: List[Zone] = field(default_factory=list)
    transit_destination: Optional[Zone] = None

    def __post_init__(self) -> None:
        if self.drone_id < 1:
            raise ValueError("drone_id must be a positive integer")

    @property
    def label(self) -> str:
        return f"D{self.drone_id}"

    @property
    def has_arrived(self) -> bool:
        return self.state == DroneState.ARRIVED

    def __repr__(self) -> str:
        return f"{self.label}@{self.current_zone.name}[{self.state.value}]"
