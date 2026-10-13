"""Reservation book for zones and connections of the Fly-in simulation."""

from typing import Dict

from ..models import Connection, Zone


class Scheduler:
    """Tracks zone occupancy and connection usage per turn.

    The start and end zones have no occupancy limit, so they are ignored.

    Attributes:
        _zone_occupants: Number of drones currently in each zone.
        _connection_reservations: For each turn, the number of drones
            using each connection.
    """

    def __init__(self) -> None:
        """Initialize the scheduler with no reservations."""
        self._zone_occupants: Dict[Zone, int] = {}
        self._connection_reservations: Dict[int, Dict[Connection, int]] = {}

    def can_reserve_zone(self, zone: Zone) -> bool:
        """Return True if the zone has room for one more drone."""
        if zone.is_start or zone.is_end:
            return True
        return self._zone_occupants.get(zone, 0) < zone.max_drones

    def occupy_zone(self, zone: Zone) -> None:
        """Add one drone to the zone."""
        if zone.is_start or zone.is_end:
            return
        self._zone_occupants[zone] = self._zone_occupants.get(zone, 0) + 1

    def release_zone(self, zone: Zone) -> None:
        """Remove one drone from the zone."""
        if zone.is_start or zone.is_end:
            return
        if zone not in self._zone_occupants:
            return
        self._zone_occupants[zone] -= 1
        if self._zone_occupants[zone] <= 0:
            del self._zone_occupants[zone]

    def can_reserve_connection(
        self, connection: Connection, turn: int
    ) -> bool:
        """Return True if the connection has capacity left in that turn."""
        actual_count = self._connection_reservations.get(turn, {}).get(
            connection, 0
        )
        return actual_count < connection.max_link_capacity

    def reserve_connection(self, connection: Connection, turn: int) -> None:
        """Add one drone to the connection usage in that turn."""
        self._connection_reservations.setdefault(turn, {}).setdefault(
            connection, 0
        )
        self._connection_reservations[turn][connection] += 1
