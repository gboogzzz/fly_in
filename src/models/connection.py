"""Connection model for the Fly-in drone routing graph.

A connection is a bidirectional edge between two zones. It also stores
how many drones may traverse it at the same time.
"""

from dataclasses import dataclass
from .zone import Zone


class InvalidConnectionError(ValueError):
    """Raised when a connection is created with invalid data.

    Examples of invalid data are a zone connected to itself or a
    non-positive link capacity. It inherits from ``ValueError`` so it can
    be caught either specifically or as a generic value error.
    """

    pass


@dataclass
class Connection:
    """Bidirectional edge between two zones of the graph.

    Two connections are considered equal when they link the same pair of
    zones, regardless of order (``a-b`` equals ``b-a``). The capacity is
    not part of the equality, so duplicates are detected even when they
    declare different capacities.

    Attributes:
        zone1: First zone of the connection, as declared in the map file.
        zone2: Second zone of the connection, as declared in the map file.
        max_link_capacity: Maximum number of drones that can traverse the
            connection simultaneously. Defaults to 1.
    """

    zone1: Zone
    zone2: Zone
    max_link_capacity: int = 1

    def __post_init__(self) -> None:
        """Validate the connection right after initialization.

        Raises:
            InvalidConnectionError: If both ends are the same zone, or if
                ``max_link_capacity`` is lower than 1.
        """
        if self.zone1 == self.zone2:
            raise InvalidConnectionError("The zone cant connect to itself")
        if self.max_link_capacity < 1:
            raise InvalidConnectionError(
                "max link capacity needs to be a positive integer, "
                f"got {self.max_link_capacity}"
            )

    def __hash__(self) -> int:
        """Return an order-independent hash of the connection.

        The hash is computed from a frozenset of both zone names, so
        ``a-b`` and ``b-a`` produce the same value. This keeps the hash
        consistent with ``__eq__`` and allows connections to be used in
        sets and as dictionary keys.

        Returns:
            The hash of the unordered pair of zone names.
        """
        return hash(frozenset({self.zone1.name, self.zone2.name}))

    def __eq__(self, other: object) -> bool:
        """Compare two connections by their unordered pair of zone names.

        Args:
            other: Object to compare with.

        Returns:
            True if both connections link the same two zones, in any
            order. ``NotImplemented`` if ``other`` is not a Connection.
        """
        if not isinstance(other, Connection):
            return NotImplemented
        return (
            {self.zone1.name, self.zone2.name} ==
            {other.zone1.name, other.zone2.name}
        )

    def involves(self, zone: Zone) -> bool:
        """Check whether the given zone is one of the connection's ends.

        Args:
            zone: Zone to look for.

        Returns:
            True if ``zone`` is ``zone1`` or ``zone2``, False otherwise.
        """
        return zone == self.zone1 or zone == self.zone2

    @property
    def name(self) -> str:
        """Return the connection name in the ``zone1-zone2`` format.

        This is the format used in the simulation output for drones in
        transit toward a restricted zone. The order follows the
        declaration in the map file.

        Returns:
            The connection name.
        """
        return f"{self.zone1.name}-{self.zone2.name}"
