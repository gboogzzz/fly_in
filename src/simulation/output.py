from typing import Dict, List
from ..models import Drone, Graph, Connection, Zone


"""Formats the simulation log as the text output of the Fly-in project."""


class OutputFormatter:
    """Converts the simulation log into output lines."""

    @staticmethod
    def format_turns(turns_log: List[Dict[Drone, str]]) -> List[str]:
        """Return one line per turn, such as ``D1-roomA D2-roomB``.

        The drones of each turn are sorted by id. Drones that did not
        move in that turn are not shown.
        """

        lines: List[str] = []

        for movements in turns_log:
            sorted_drones = sorted(movements.keys(), key=lambda d: d.drone_id)
            parts: List[str] = []
            for drone in sorted_drones:
                destiny = movements[drone]
                parts.append(f"{drone.label}-{destiny}")
            line = " ".join(parts)
            lines.append(line)

        return lines

    @staticmethod
    def format_capacity(graph: Graph, zones: Dict[Zone, int], connections: Dict[Connection, int]) -> List[str]:
        lines = []

        for zone in graph.zones:
            if zone.is_start or zone.is_end:
                continue
            used = zones.get(zone, 0)
            lines.append(f"Zone {zone.name}: {used}/{zone.max_drones} drones")

        for c in graph.connections:
            used = connections.get(c, 0)
            lines.append(f"Connection {c.name}: {used}/{c.max_link_capacity} capacity used")

        return lines