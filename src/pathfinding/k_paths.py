"""K shortest paths search (Yen's algorithm) for the Fly-in project."""

import copy
from typing import List, Tuple
from ..models import Graph, Zone, ZoneType
from .dijkstra import Dijkstra, PathNotFoundError


class KPaths:
    """Finds several low cost paths between two zones."""

    @staticmethod
    def find_k_paths(
        graph: Graph, start: Zone, end: Zone, k: int
    ) -> List[List[Zone]]:
        """Return up to k loopless paths from start to end, cheapest first.

        Uses Yen's algorithm: for each node of the last accepted path, it
        keeps the path up to that node and searches a new way to the end
        on a graph copy, without the links already used from that node and
        without the zones before it. The cheapest candidate is accepted.

        Raises:
            PathNotFoundError: If end cannot be reached from start.
        """
        A: List[List[Zone]] = []   # acepted paths
        B: List[List[Zone]] = []   # candidates to chose

        A.append(Dijkstra.find_path(graph, start, end))

        while len(A) < k:
            last_path = A[-1]
            for i, spur_node in enumerate(last_path[:-1]):
                root_path = last_path[0:i + 1]
                graph_copy = copy.deepcopy(graph)
                spur_in_copy = graph_copy.get_zone(spur_node.name)

                for path in A:
                    if path[0:i + 1] == root_path and len(path) > i + 1:
                        next_in_copy = graph_copy.get_zone(
                            path[i + 1].name
                        )
                        graph_copy.remove_neighbor(
                            spur_in_copy, next_in_copy
                        )

                for node in root_path[:-1]:
                    zone = graph_copy.get_zone(node.name)
                    zone.zone_type = ZoneType.BLOCKED

                try:
                    spur_path = Dijkstra.find_path(
                        graph_copy, spur_in_copy, end
                    )

                    candidate = root_path[:-1] + spur_path
                    if candidate not in A and candidate not in B:
                        B.append(candidate)
                except PathNotFoundError:
                    continue

            if not B:
                break
            B.sort(key=lambda path: KPaths._path_cost(path))
            best = B.pop(0)
            A.append(best)

        return A

    @staticmethod
    def _path_cost(path: List[Zone]) -> Tuple[int, int]:
        """Return the cost of a path as (turns, priority bonus).

        The start zone is not counted, because the cost is paid when
        entering a zone. A lower bonus means more priority zones.
        """
        turns = 0
        bonus = 0
        for zone in path[1:]:
            zone_turns, zone_bonus = Dijkstra.step_cost(zone)
            turns += zone_turns
            bonus += zone_bonus
        return (turns, bonus)
