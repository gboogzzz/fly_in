"""Graph model for the Fly-in drone routing simulation.

The graph stores the zones (nodes) and connections (edges) of a map. It
uses an adjacency list for fast neighbour lookups, which suits the
sparse maps of this project (O(V + E) memory).
"""

from typing import Optional, List, Dict, Set
from .zone import Zone
from .connection import Connection


class ZoneNotFoundError(KeyError):
    """Raised when a zone is looked up but does not exist in the graph."""

    pass


class DuplicateConnectionError(ValueError):
    """Raised when the same connection is added to the graph twice.

    Connections are bidirectional, so ``a-b`` and ``b-a`` are considered
    duplicates.
    """

    pass


class Graph:
    """Undirected graph of zones linked by connections.

    Zones are indexed by name for O(1) lookup, and each zone keeps a list
    of accessible neighbours. Blocked zones are never added as neighbours,
    so pathfinding algorithms never consider them.

    Attributes:
        _zones: Mapping from zone name to Zone.
        _neighbours: Adjacency list mapping each zone to the accessible
            zones it is connected to.
        _connections: Set of all connections, used to detect duplicates
            in O(1).
        _start_zone: The start zone, or None until it is added.
        _end_zone: The end zone, or None until it is added.
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._zones: Dict[str, Zone] = {}
        self._neighbours: Dict[Zone, List[Zone]] = {}
        self._connections: Set[Connection] = set()
        self._start_zone: Optional[Zone] = None
        self._end_zone: Optional[Zone] = None

    def add_zone(self, zone: Zone) -> None:
        """Add a zone to the graph.

        The zone gets an empty neighbour list. If it is the start or the
        end zone, it is also stored as such.

        Args:
            zone: Zone to add.

        Raises:
            ValueError: If a zone with the same name already exists.
        """
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
        """Add a bidirectional connection between two existing zones.

        Each zone is added as a neighbour of the other only if it is
        accessible (not blocked). The connection itself is always stored,
        even when one of its ends is blocked.

        Args:
            connection: Connection to add.

        Raises:
            DuplicateConnectionError: If the connection already exists,
                in either direction.
            ValueError: If one of the zones is not in the graph.
        """
        if connection in self._connections:
            raise DuplicateConnectionError("cant have duplicate connections")
        if connection.zone1.name not in self._zones:
            raise ValueError(f"{connection.zone1.name} not found in graph")
        if connection.zone2.name not in self._zones:
            raise ValueError(f"{connection.zone2.name} not found in graph")
        self._connections.add(connection)
        if connection.zone2.zone_type.is_accessible():
            self._neighbours[connection.zone1].append(connection.zone2)
        if connection.zone1.zone_type.is_accessible():
            self._neighbours[connection.zone2].append(connection.zone1)

    def get_zone(self, name: str) -> Zone:
        """Return the zone with the given name.

        Args:
            name: Name of the zone.

        Returns:
            The matching zone.

        Raises:
            ZoneNotFoundError: If no zone has that name.
        """
        if name not in self._zones:
            raise ZoneNotFoundError(f"zone '{name}' not found in graph")
        return self._zones[name]

    def get_neighbors(self, zone: Zone) -> List[Zone]:
        """Return the accessible neighbours of a zone.

        Note that the internal list is returned, not a copy, so it must
        not be modified by the caller.

        Args:
            zone: Zone whose neighbours are requested.

        Returns:
            The list of accessible zones connected to ``zone``.

        Raises:
            ZoneNotFoundError: If the zone is not in the graph.
        """
        if zone not in self._neighbours:
            raise ZoneNotFoundError(f"zone '{zone.name}' not found in graph")
        return self._neighbours[zone]

    def remove_neighbor(self, zone1: Zone, zone2: Zone) -> None:
        """Remove the adjacency between two zones, in both directions.

        Only the adjacency list is updated; the connection stays in the
        connection set. Missing entries are ignored.

        Args:
            zone1: First zone.
            zone2: Second zone.
        """
        if zone1 in self._neighbours and zone2 in self._neighbours[zone1]:
            self._neighbours[zone1].remove(zone2)
        if zone2 in self._neighbours and zone1 in self._neighbours[zone2]:
            self._neighbours[zone2].remove(zone1)

    def get_connection(self, zone1: Zone, zone2: Zone) -> Optional[Connection]:
        """Return the connection linking two zones, in any order.

        This performs a linear search over all connections, O(E).

        Args:
            zone1: First zone.
            zone2: Second zone.

        Returns:
            The connection between both zones, or None if there is none.
        """
        for connect in self._connections:
            if (connect.involves(zone1) and connect.involves(zone2)):
                return connect
        return None

    @property
    def start_zone(self) -> Zone:
        """Return the start zone of the graph.

        Returns:
            The start zone.

        Raises:
            ValueError: If no start zone has been added.
        """
        if self._start_zone is None:
            raise ValueError("start zone not defined in graph")
        return self._start_zone

    @property
    def end_zone(self) -> Zone:
        """Return the end zone of the graph.

        Returns:
            The end zone.

        Raises:
            ValueError: If no end zone has been added.
        """
        if self._end_zone is None:
            raise ValueError("end zone not defined in graph")
        return self._end_zone

    @property
    def zone_count(self) -> int:
        """Return the number of zones in the graph."""
        return len(self._zones)

    @property
    def connection_count(self) -> int:
        """Return the number of connections in the graph."""
        return len(self._connections)

    @property
    def zones(self) -> List[Zone]:
        """Return a copy of the list of zones, in insertion order."""
        return list(self._zones.values())

    @property
    def connections(self) -> List[Connection]:
        """Return a copy of the list of connections."""
        return list(self._connections)
