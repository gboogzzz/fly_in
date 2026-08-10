from typing import Dict, List
from ..models import Graph, Zone, Drone
from .k_paths import KPaths


class Router:
    @staticmethod
    def route(
        graph: Graph, start: Zone, end: Zone, nb_drones: int
    ) -> Dict[Drone, List[Zone]]:
        paths = Router._find_sufficient_paths(graph, start, end, nb_drones)
        distribution = Router._distribute_drones(graph, paths, nb_drones)
        result: Dict[Drone, List[Zone]] = {}
        drone_id = 1

        for index, count in distribution.items():
            path = paths[index]
            for _ in range(count):
                drone = Drone(
                    drone_id=drone_id, current_zone=start, path=path
                )
                result[drone] = path
                drone_id += 1

        return result

    @staticmethod
    def _find_sufficient_paths(
        graph: Graph, start: Zone, end: Zone, nb_drones: int
    ) -> List[List[Zone]]:
        k = 1
        paths = KPaths.find_k_paths(graph, start, end, k)
        capacities = [Router._path_capacity(graph, path) for path in paths]
        total_capacity = sum(capacities)

        while total_capacity < nb_drones:
            k += 1
            new_paths = KPaths.find_k_paths(graph, start, end, k)
            if len(new_paths) == len(paths):
                # KPaths didn't find any new path
                break
            paths = new_paths
            capacities = [
                Router._path_capacity(graph, path) for path in paths
            ]
            total_capacity = sum(capacities)

        return paths

    @staticmethod
    def _path_capacity(graph: Graph, path: List[Zone]) -> int:
        capacities: List[int] = []
        for zone in path[1:]:
            capacities.append(zone.max_drones)
        for i in range(len(path) - 1):
            connection = graph.get_connection(path[i], path[i + 1])
            if connection is None:
                raise ValueError(
                    f"No connection between '{path[i].name}' "
                    f"and '{path[i + 1].name}'"
                )
            capacities.append(connection.max_link_capacity)

        return min(capacities)

    @staticmethod
    def _distribute_drones(
        graph: Graph, paths: List[List[Zone]], nb_drones: int
    ) -> Dict[int, int]:
        capacities = [Router._path_capacity(graph, p) for p in paths]
        total_capacity = sum(capacities)
        distribution: Dict[int, int] = {}
        drones_attributed = 0
        for i, capacity in enumerate(capacities):
            proportion = capacity / total_capacity
            qty = int(proportion * nb_drones)
            distribution[i] = qty
            drones_attributed += qty
        rest = nb_drones - drones_attributed
        if rest > 0:
            distribution[capacities.index(max(capacities))] += rest

        return distribution
