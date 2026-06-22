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

    def get_zone(self, name: str) -> Zone:
        if name not in self._zones:
            raise ZoneNotFoundError(f"zone '{name}' not found in graph")
        return self._zones[name]

    def get_neighbors(self, zone: Zone) -> List[Zone]:
        if zone not in self._neighbours:
            raise ZoneNotFoundError(f"zone '{zone.name}' not found in graph")
        return self._neighbours[zone]

    def get_connection(self, zone1: Zone, zone2: Zone) -> Optional[Connection]:
        for connect in self._connections:
            if (connect.involves(zone1) and connect.involves(zone2)):
                return connect
        return None

    @property
    def start_zone(self) -> Zone:
        if self._start_zone is None:
            raise ValueError("start zone not defined in graph")
        return self._start_zone

    @property
    def end_zone(self) -> Zone:
        if self._end_zone is None:
            raise ValueError("end zone not defined in graph")
        return self._end_zone

    @property
    def zone_count(self) -> int:
        return len(self._zones)

    @property
    def connection_count(self) -> int:
        return len(self._connections)
