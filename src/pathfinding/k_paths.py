import copy
from typing import List
from ..models import Graph, Zone, ZoneType
from .dijkstra import Dijkstra, PathNotFoundError


class KPaths:
    @staticmethod
    def find_k_paths(graph: Graph, start: Zone, end: Zone, k: int) -> List[List[Zone]]:
        A: List[List[Zone]] = []   # acepted paths
        B: List[List[Zone]] = []   # candidates to chose

        A.append(Dijkstra.find_path(graph, start, end))

        while len(A) < k:
            last_path = A[-1]
            for i, spur_node in enumerate(last_path[:-1]):
                root_path = last_path[0 : i + 1]
                graph_copy = copy.deepcopy(graph)
                for path in A:
                    if path[0:i+1] == root_path and len(path) > i+1:
                        zone_to_block = path[i+1]
                        zone_in_copy = graph_copy.get_zone(zone_to_block.name)
                        zone_in_copy.zone_type = ZoneType.BLOCKED
                for node in root_path[:-1]:
                    if node == spur_node:
                        continue
                    zone = graph_copy.get_zone(node.name)
                    zone.zone_type = ZoneType.BLOCKED
                try:
                    spur_node_copy = graph_copy.get_zone(spur_node.name)
                    spur_path = Dijkstra.find_path(graph_copy, spur_node_copy, end)

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
    def _path_cost(path: List[Zone]) -> int:
        total = 0
        for zone in path[1:]:
            total += zone.zone_type.movement_cost()
        return total


