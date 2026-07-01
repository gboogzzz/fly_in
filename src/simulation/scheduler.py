from ..models import Connection, Zone
from typing import Dict

class Scheduler:
    def __init__(self) -> None:
        self._zone_reservations: Dict[int, Dict[Zone, int]] = {}
        #extern key is the turn number
        #intern key is the Zone
        #value is the amount of reservations made to that zone on this turn
        self._connection_reservations: Dict[int, Dict[Connection, int]] = {}
        #same as the other but with connections

    def can_reserve_zone(self, zone: Zone, turn: int) -> bool:
        if zone.is_start or zone.is_end:
            return True
        actual_count = self._zone_reservations.get(turn, {}).get(zone, 0)

        return actual_count < zone.max_drones
    
    def reserve_zone(self, zone: Zone, turn: int) -> None:
        if zone.is_start or zone.is_end:
            return
        self._zone_reservations.setdefault(turn, {}).setdefault(zone, 0)
        self._zone_reservations[turn][zone] += 1
    

    def can_reserve_connection(self, connection: Connection, turn: int) -> bool:
        actual_count = self._connection_reservations.get(turn, {}).get(connection, 0)

        return actual_count < connection.max_link_capacity


    def reserve_connection(self, connection: Connection, turn: int) -> None:
        self._connection_reservations.setdefault(turn, {}).setdefault(connection, 0)
        self._connection_reservations[turn][connection] += 1