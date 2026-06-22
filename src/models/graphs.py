from typing import Optional, List, Dict, Set
from .zone import Zone
from .connection import Connection


class ZoneNotFoundError(KeyError):
    pass


class DuplicateConnectionError(ValueError):
    pass


class Graph:
    def __init__(self) -> None:
        self._zones: Dict[str, Zone] = {}
        self._neighbours: Dict[Zone, List[Zone]] = {}
        self._connections: Set[Connection] = set()
        self._start_zone: Optional[Zone] = None
        self._end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        if zone.name in self._zones:
            raise ValueError("cant have duplicate zones")
        else:
            self._zones[zone.name] = zone
            self._neighbours[zone] = []
            if zone.is_start:
                self._start_zone = zone
            elif zone.is_end:
                self._end_zone = zone
    
    def add_connection(self, connection: Connection) -> None:
        if connection in self._connections:
            raise DuplicateConnectionError("cant have duplicate connections")
        if connection.zone1.name not in self._zones:
            raise ValueError(f"{connection.zone1.name} not found in graph")
        if connection.zone2.name not in self._zones:
            raise ValueError(f"{connection.zone2.name} not found in graph")
        self._connections.add(connection)
        if connection.zone1.zone_type.is_accessible():
            self._neighbours[connection.zone1].append(connection.zone2)
        if connection.zone2.zone_type.is_accessible():
            self._neighbours[connection.zone2].append(connection.zone1)