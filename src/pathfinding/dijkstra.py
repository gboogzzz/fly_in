
import heapq
from typing import Dict, List, Optional, Tuple
from ..models import Graph, Zone, ZoneType


class PathNotFoundError(Exception):
    def __init__(self, start: Zone, end: Zone) -> None:
        self.start = start
        self.end = end
        super().__init__(f"No path found from '{start.name}' to '{end.name}'")


class Dijkstra:
    @staticmethod
    def find_path(graph: Graph, start: Zone, end: Zone) -> List[Zone]:
        _, previous = Dijkstra._compute_distances(graph, start, end)

        return Dijkstra._reconstruct_path(previous, start, end)
    

    @staticmethod
    def _compute_distances(graph: Graph, start: Zone, end: Zone) -> Tuple[Dict[Zone, int], Dict[Zone, Optional[Zone]]]:
        distances: Dict[Zone, int] = {start: 0}
        previous: Dict[Zone, Optional[Zone]] = {}
        counter = 0
        queue: List[Tuple[int, str, int, Zone]] = []
        heapq.heappush(queue, (0, start.name, counter, start))

        while queue:
            actual_distance, _, _, actual_zone = heapq.heappop(queue)

            if actual_zone.is_end:
                break
            if actual_distance > distances.get(actual_zone, float('inf')):
                continue
            for neighbour in graph.get_neighbors(actual_zone):
                if neighbour.zone_type == ZoneType.BLOCKED:
                    continue
                cost = neighbour.zone_type.movement_cost()
                new_distance = actual_distance + cost
                if new_distance < distances.get(neighbour, float('inf')):
                    distances[neighbour] = new_distance
                    previous[neighbour] = actual_zone
                    counter += 1
                    heapq.heappush(queue, (new_distance, neighbour.name, counter, neighbour))

        return distances, previous
    

    @staticmethod
    def _reconstruct_path(previous: Dict[Zone, Optional[Zone]], start: Zone, end: Zone) -> List[Zone]:
        if end not in previous and end != start:
            raise PathNotFoundError(start, end)
        path = [end]
        actual = end
        while actual != start:
            actual = previous[actual]
            path.append(actual)

        path.reverse()
        return path