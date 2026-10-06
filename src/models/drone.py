"""Drone model for the Fly-in drone routing simulation.

Defines the possible states of a drone and the Drone class, which holds
the position, state and planned path of each drone during the simulation.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List
from .zone import Zone


class DroneState(Enum):
    """Possible states of a drone during the simulation.

    Attributes:
        WAITING: The drone is stationary in a zone, either before leaving
            the start or while strategically waiting for free capacity.
        MOVING: The drone moved to an adjacent zone during the turn.
        IN_TRANSIT: The drone is on a connection toward a restricted zone
            and must reach it on the next turn.
        ARRIVED: The drone reached the end zone and is no longer tracked.
    """

    WAITING = "waiting"
    MOVING = "moving"
    IN_TRANSIT = "in_transit"
    ARRIVED = "arrived"


@dataclass
class Drone:
    """A single drone travelling from the start zone to the end zone.

    Two drones are considered equal when they share the same ID. The hash
    depends only on the ID, which never changes, so a drone can safely be
    used in sets and as a dictionary key even though its position and
    state change every turn.

    Attributes:
        drone_id: Unique positive identifier of the drone (1, 2, 3...).
        current_zone: Zone where the drone is currently located.
        state: Current state of the drone. Defaults to WAITING.
        path: Ordered list of zones the drone plans to traverse. Each
            drone gets its own new list through ``default_factory``.
        transit_destination: Restricted zone the drone is flying toward
            while IN_TRANSIT, or None when it is not in transit.
    """

    drone_id: int
    current_zone: Zone
    state: DroneState = DroneState.WAITING
    path: List[Zone] = field(default_factory=list)
    transit_destination: Optional[Zone] = None

    def __post_init__(self) -> None:
        """Validate the drone right after initialization.

        Raises:
            ValueError: If ``drone_id`` is lower than 1.
        """
        if self.drone_id < 1:
            raise ValueError("drone_id must be a positive integer")

    @property
    def label(self) -> str:
        """Return the drone label used in the simulation output.

        Returns:
            The label in the ``D<ID>`` format (e.g. ``D1``).
        """
        return f"D{self.drone_id}"

    @property
    def has_arrived(self) -> bool:
        """Check whether the drone has reached the end zone.

        Returns:
            True if the drone state is ARRIVED, False otherwise.
        """
        return self.state == DroneState.ARRIVED

    def __repr__(self) -> str:
        """Return a compact representation of the drone for debugging.

        Returns:
            A string in the ``D<ID>@<zone>[<state>]`` format
            (e.g. ``D3@roof1[waiting]``).
        """
        return f"{self.label}@{self.current_zone.name}[{self.state.value}]"

    def __hash__(self) -> int:
        """Return a hash based only on the drone ID.

        The ID never changes during the simulation, so the hash stays
        stable even when the drone moves or changes state.

        Returns:
            The hash of ``drone_id``.
        """
        return hash(self.drone_id)

    def __eq__(self, other: object) -> bool:
        """Compare two drones by their ID.

        Args:
            other: Object to compare with.

        Returns:
            True if both drones have the same ID. ``NotImplemented`` if
            ``other`` is not a Drone.
        """
        if not isinstance(other, Drone):
            return NotImplemented
        return self.drone_id == other.drone_id
