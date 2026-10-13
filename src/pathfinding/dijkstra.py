"""Dijkstra shortest path search for the Fly-in drone routing project."""

import heapq
from typing import Dict, List, Optional, Tuple
from ..models import Graph, Zone, ZoneType


class PathNotFoundError(Exception):
    """Raised when the end zone cannot be reached from the start zone."""

    def __init__(self, start: Zone, end: Zone) -> None:
        """Store the start and end zones and build the error message."""
        self.start = start
        self.end = end
        super().__init__(
            f"No path found from '{start.name}' to '{end.name}'"
        )


class Dijkstra:
    """Finds the lowest cost path between two zones."""

    @staticmethod
    def find_path(graph: Graph, start: Zone, end: Zone) -> List[Zone]:
        """Return the cheapest path from start to end, both included.

        Raises:
            PathNotFoundError: If end cannot be reached from start.
        """
        _, previous = Dijkstra._compute_distances(graph, start, end)

        return Dijkstra._reconstruct_path(previous, start, end)

    @staticmethod
    def step_cost(zone: Zone) -> Tuple[int, int]:
        """Return the cost of entering a zone as (turns, priority bonus).

        The bonus is -1 for priority zones and 0 for the others, so a
        lower total means more priority zones on the path.
        """
        bonus = -1 if zone.zone_type == ZoneType.PRIORITY else 0
        return (zone.zone_type.movement_cost(), bonus)

    @staticmethod
    def _compute_distances(
        graph: Graph, start: Zone, end: Zone
    ) -> Tuple[Dict[Zone, Tuple[int, int]], Dict[Zone, Optional[Zone]]]:
        """Compute the lowest cost and the previous zone for each zone.

        Queue entries are (cost, name, counter, zone): the name makes ties
        deterministic and the counter avoids comparing two zones.
        Stops when the end zone leaves the queue.

        Returns:
            A tuple (distances, previous) with the lowest known cost to
            each discovered zone and the zone it was reached from.
        """
        distances: Dict[Zone, Tuple[int, int]] = {start: (0, 0)}
        previous: Dict[Zone, Optional[Zone]] = {}
        counter = 0
        queue: List[Tuple[Tuple[int, int], str, int, Zone]] = []
        heapq.heappush(queue, ((0, 0), start.name, counter, start))

        while queue:
            actual_cost, _, _, actual_zone = heapq.heappop(queue)

            if actual_zone.is_end:
                break
            if actual_cost > distances[actual_zone]:
                continue
            for neighbour in graph.get_neighbors(actual_zone):
                if neighbour.zone_type == ZoneType.BLOCKED:
                    continue
                turns, bonus = Dijkstra.step_cost(neighbour)
                new_cost = (actual_cost[0] + turns, actual_cost[1] + bonus)
                known = distances.get(neighbour)
                if known is None or new_cost < known:
                    distances[neighbour] = new_cost
                    previous[neighbour] = actual_zone
                    counter += 1
                    heapq.heappush(
                        queue,
                        (new_cost, neighbour.name, counter, neighbour),
                    )

        return distances, previous

    @staticmethod
    def _reconstruct_path(
        previous: Dict[Zone, Optional[Zone]], start: Zone, end: Zone
    ) -> List[Zone]:
        """Walk back from end to start through previous and reverse it.

        Raises:
            PathNotFoundError: If end was never reached.
        """
        if end not in previous:
            raise PathNotFoundError(start, end)
        path = [end]
        actual = end
        while actual != start:
            prev_zone = previous[actual]
            assert prev_zone is not None
            actual = prev_zone
            path.append(actual)

        path.reverse()
        return path
