"""Turn by turn simulation engine for the Fly-in project."""

from typing import Dict, List, Tuple, Optional, Set

from ..models import Graph, Drone, Zone, DroneState, ZoneType, Connection
from .scheduler import Scheduler


class SimulationDeadlockError(RuntimeError):
    """Raised when no drone can move and none is in transit."""


class TurnEngine:
    """Runs the simulation one turn at a time.

    Attributes:
        graph: The map graph.
        scheduler: Keeps the zone and connection reservations.
        drones: All the drones of the simulation.
        in_transit: Drones travelling to a restricted zone, mapped to
            (connection, destination zone, arrival turn).
    """

    def __init__(
        self, graph: Graph, drone_paths: Dict[Drone, List[Zone]]
    ) -> None:
        """Create the engine for a graph and the path of each drone."""
        self.graph = graph
        self.scheduler = Scheduler()
        self.drones = list(drone_paths.keys())
        self.in_transit: Dict[Drone, Tuple[Connection, Zone, int]] = {}
        self.capacity_log: List[Tuple[Dict[Zone, int], Dict[Connection, int]]] = []

    def run(self) -> List[Dict[Drone, str]]:
        """Run turns until every drone has arrived.

        Returns:
            One dict per turn, mapping each drone that moved to its
            destination zone (or connection, when entering a
            restricted zone).

        Raises:
            SimulationDeadlockError: If nobody can move and nobody is
                in transit.
        """
        turns_log: List[Dict[Drone, str]] = []
        turn = 1

        while not all(d.state == DroneState.ARRIVED for d in self.drones):
            movements = self._process_turn(turn)
            if not movements and not self.in_transit:
                raise SimulationDeadlockError(
                    f"simulation deadlocked at turn {turn}: no drone can "
                    "move and none are in transit"
                )
            turns_log.append(movements)
            self.capacity_log.append((self.scheduler.zone_usage(), self.scheduler.connection_usage(turn)))
            turn += 1

        return turns_log

    def _process_turn(self, turn: int) -> Dict[Drone, str]:
        """Simulate one turn and return the movements made.

        First lands the drones whose transit ends now, then tries to
        move each remaining drone to its next zone. A drone that
        cannot reserve the connection and the zone waits.

        Raises:
            ValueError: If two consecutive zones are not connected.
        """
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
                # The connection is occupied for the whole transit (both
                # turns), and the destination zone slot is claimed now,
                # ahead of time, so the drone is guaranteed a place when
                # it lands - it can't "wait" once committed to a transit.
                can_reserve = (
                    self.scheduler.can_reserve_connection(
                        next_connection, turn
                    )
                    and self.scheduler.can_reserve_connection(
                        next_connection, arrival_turn
                    )
                    and self.scheduler.can_reserve_zone(next_zone)
                )
                if can_reserve:
                    self.scheduler.reserve_connection(
                        next_connection, turn
                    )
                    self.scheduler.reserve_connection(
                        next_connection, arrival_turn
                    )
                    self.scheduler.release_zone(drone.current_zone)
                    self.scheduler.occupy_zone(next_zone)

                    self.in_transit[drone] = (
                        next_connection, next_zone, arrival_turn
                    )
                    movements[drone] = next_connection.name
            else:
                can_reserve = (
                    self.scheduler.can_reserve_connection(
                        next_connection, turn
                    )
                    and self.scheduler.can_reserve_zone(next_zone)
                )
                if can_reserve:
                    self.scheduler.reserve_connection(next_connection, turn)
                    self.scheduler.release_zone(drone.current_zone)
                    self.scheduler.occupy_zone(next_zone)

                    drone.current_zone = next_zone
                    movements[drone] = next_zone.name
                    if next_zone.is_end:
                        drone.state = DroneState.ARRIVED

        return movements

    def _get_next_zone(self, drone: Drone) -> Optional[Zone]:
        """Return the next zone in the drone path, or None at the end."""
        index = drone.path.index(drone.current_zone)
        if index + 1 >= len(drone.path):
            return None
        return drone.path[index + 1]
