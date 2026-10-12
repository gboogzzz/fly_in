"""Router that assigns each drone to a path for the Fly-in project."""

from typing import Dict, List
from ..models import Graph, Zone, Drone
from .k_paths import KPaths


class Router:
    """Chooses paths for the drones and distributes the drones by them."""

    @staticmethod
    def route(
        graph: Graph, start: Zone, end: Zone, nb_drones: int
    ) -> Dict[Drone, List[Zone]]:
        """Create the drones and assign a path to each one.

        Returns:
            A dict mapping each drone to its path (start to end).

        Raises:
            PathNotFoundError: If end cannot be reached from start.
        """
        paths = Router._find_sufficient_paths(graph, start, end, nb_drones)
        distribution = Router._distribute_drones(graph, paths, nb_drones)
        result: Dict[Drone, List[Zone]] = {}
        drone_id = 1

        for index, count in distribution.items():
            path = paths[index]
            for _ in range(count):
                drone = Drone(
                    drone_id=drone_id, current_zone=start, path=list(path)
                )
                result[drone] = path
                drone_id += 1

        return result

    @staticmethod
    def _find_sufficient_paths(
        graph: Graph, start: Zone, end: Zone, nb_drones: int
    ) -> List[List[Zone]]:
        """Return enough paths for their total capacity to fit all drones.

        Increases k until the capacity is enough or no new path is found.
        """
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
        """Return how many drones a path allows at the same time.

        It is the minimum of max_drones of the intermediate zones and
        max_link_capacity of the connections. Start and end are ignored
        as zones because they have no occupancy limit.

        Raises:
            ValueError: If two consecutive zones are not connected.
        """
        capacities: List[int] = []
        for zone in path[1:-1]:
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
        """Split the drones across the paths, proportionally to capacity.

        Leftover drones from rounding go to the path with most capacity.

        Returns:
            A dict mapping each path index to its number of drones.
        """
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
