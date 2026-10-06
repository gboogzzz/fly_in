"""Zone model for the Fly-in drone routing simulation.

Defines the zone types with their movement rules and the Zone class,
which represents a node of the graph.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class InvalidZoneTypeError(ValueError):
    """Raised when a map file declares a zone type that does not exist."""

    pass


class InaccessibleZoneError(Exception):
    """Raised when a movement cost is requested for a blocked zone.

    Blocked zones are filtered out of the graph adjacency, so this error
    indicates an internal bug rather than an invalid input.
    """

    pass


class ZoneType(Enum):
    """Types of zone and their movement rules.

    The values match the text used in the map files, so a type can be
    built directly from the file with ``ZoneType("restricted")``.

    Attributes:
        NORMAL: Standard zone, entering it costs 1 turn.
        BLOCKED: Inaccessible zone, drones can never enter it.
        RESTRICTED: Dangerous zone, entering it costs 2 turns.
        PRIORITY: Preferred zone, entering it costs 1 turn. The
            preference itself is handled by the pathfinding algorithm.
    """

    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"

    def movement_cost(self) -> int:
        """Return the number of turns needed to enter a zone of this type.

        Returns:
            2 for restricted zones, 1 for normal and priority zones.

        Raises:
            InaccessibleZoneError: If the zone type is BLOCKED.
        """
        if self == ZoneType.BLOCKED:
            raise InaccessibleZoneError(
                "blocked zone doesnt have cost - is invalid"
            )
        elif self == ZoneType.RESTRICTED:
            return 2
        else:
            return 1

    def is_accessible(self) -> bool:
        """Check whether drones can enter a zone of this type.

        Returns:
            False for blocked zones, True otherwise.
        """
        return self != ZoneType.BLOCKED


@dataclass
class Zone:
    """A zone (node) of the graph where drones can be located.

    Two zones are considered equal when they have the same name. The hash
    depends only on the name, which is unique and never changes, so zones
    can be used as dictionary keys (e.g. in the graph adjacency list).

    Attributes:
        name: Unique name of the zone, without dashes or spaces.
        x: Horizontal coordinate, used by the visual representation.
        y: Vertical coordinate, used by the visual representation.
        zone_type: Type of the zone. Defaults to NORMAL.
        max_drones: Maximum number of drones the zone can hold at the
            same time. Defaults to 1. Not enforced for the start and end
            zones.
        color: Optional color used by the visual representation.
        is_start: True if this is the start zone.
        is_end: True if this is the end zone.
    """

    name: str
    x: int
    y: int
    zone_type: ZoneType = ZoneType.NORMAL
    max_drones: int = 1
    color: Optional[str] = None
    is_start: bool = False
    is_end: bool = False

    def __post_init__(self) -> None:
        """Validate the zone right after initialization.

        Raises:
            ValueError: If the name is empty, contains a dash or a space,
                or if ``max_drones`` is lower than 1.
        """
        if not self.name:
            raise ValueError("zone name cant be empty")
        if self.max_drones < 1:
            raise ValueError("max_drones needs to be an integer and positive")
        if "-" in self.name or " " in self.name:
            raise ValueError(f"invalid '{self.name}' name:"
                             " cant have '-' or spaces")

    def __hash__(self) -> int:
        """Return a hash based only on the zone name.

        Returns:
            The hash of ``name``.
        """
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Compare two zones by their name.

        Args:
            other: Object to compare with.

        Returns:
            True if both zones have the same name. ``NotImplemented`` if
            ``other`` is not a Zone.
        """
        if not isinstance(other, Zone):
            return NotImplemented
        return self.name == other.name
