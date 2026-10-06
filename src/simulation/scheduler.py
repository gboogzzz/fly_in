from typing import Dict

from ..models import Connection, Zone


class Scheduler:

    def __init__(self) -> None:
        self._zone_occupants: Dict[Zone, int] = {}
        self._connection_reservations: Dict[int, Dict[Connection, int]] = {}

    def can_reserve_zone(self, zone: Zone) -> bool:
        if zone.is_start or zone.is_end:
            return True
        return self._zone_occupants.get(zone, 0) < zone.max_drones

    def occupy_zone(self, zone: Zone) -> None:
        if zone.is_start or zone.is_end:
            return
        self._zone_occupants[zone] = self._zone_occupants.get(zone, 0) + 1

    def release_zone(self, zone: Zone) -> None:
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
        actual_count = self._connection_reservations.get(turn, {}).get(
            connection, 0
        )
        return actual_count < connection.max_link_capacity

    def reserve_connection(self, connection: Connection, turn: int) -> None:
        self._connection_reservations.setdefault(turn, {}).setdefault(
            connection, 0
        )
        self._connection_reservations[turn][connection] += 1
