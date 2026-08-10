from typing import Dict, List, Tuple, Optional, Set
from ..models import Graph, Drone, Zone, DroneState, ZoneType, Connection
from .scheduler import Scheduler


class TurnEngine:
    def __init__(
        self, graph: Graph, drone_paths: Dict[Drone, List[Zone]]
    ) -> None:
        self.graph = graph
        self.scheduler = Scheduler()
        self.drones = list(drone_paths.keys())
        self.in_transit: Dict[Drone, Tuple[Connection, Zone, int]] = {}

    def run(self) -> List[Dict[Drone, str]]:
        turns_log: List[Dict[Drone, str]] = []
        turn = 1

        while not all(d.state == DroneState.ARRIVED for d in self.drones):
            movements = self._process_turn(turn)
            turns_log.append(movements)
            turn += 1

        return turns_log

    def _process_turn(self, turn: int) -> Dict[Drone, str]:
        movements: Dict[Drone, str] = {}
        arrived_this_turn: Set[Drone] = set()

        for drone in list(self.in_transit.keys()):
            connection, destination, arrival_turn = self.in_transit[drone]
            if turn == arrival_turn:
                drone.current_zone = destination
                movements[drone] = destination.name
                del self.in_transit[drone]
                arrived_this_turn.add(drone)
                if destination.is_end:
                    drone.state = DroneState.ARRIVED

        for drone in self.drones:
            if drone.state == DroneState.ARRIVED:
                continue
            if drone in self.in_transit:
                continue
            if drone in arrived_this_turn:
                continue
            next_zone = self._get_next_zone(drone)
            if next_zone is None:
                continue
            next_connection = self.graph.get_connection(
                drone.current_zone, next_zone
            )
            if next_connection is None:
                raise ValueError(
                    f"No connection between '{drone.current_zone.name}' "
                    f"and '{next_zone.name}'"
                )
            if next_zone.zone_type == ZoneType.RESTRICTED:
                arrival_turn = turn + 1
                can_reserve = (
                    self.scheduler.can_reserve_connection(
                        next_connection, turn
                    )
                    and self.scheduler.can_reserve_zone(
                        next_zone, arrival_turn
                    )
                )
                if can_reserve:
                    self.scheduler.reserve_connection(
                        next_connection, turn
                    )
                    self.scheduler.reserve_zone(next_zone, arrival_turn)

                    self.in_transit[drone] = (
                        next_connection, next_zone, arrival_turn
                    )
                    movements[drone] = next_connection.name
            else:
                can_reserve = (
                    self.scheduler.can_reserve_connection(
                        next_connection, turn
                    )
                    and self.scheduler.can_reserve_zone(next_zone, turn)
                )
                if can_reserve:
                    self.scheduler.reserve_connection(next_connection, turn)
                    self.scheduler.reserve_zone(next_zone, turn)

                    drone.current_zone = next_zone
                    movements[drone] = next_zone.name
                    if next_zone.is_end:
                        drone.state = DroneState.ARRIVED

        return movements

    def _get_next_zone(self, drone: Drone) -> Optional[Zone]:
        index = drone.path.index(drone.current_zone)
        if index + 1 >= len(drone.path):
            return None
        return drone.path[index + 1]
