import sys

from src.parser.map_parser import MapParser, ParseError
from src.pathfinding.router import Router
from src.pathfinding.dijkstra import PathNotFoundError
from src.simulation.engine import TurnEngine, SimulationDeadlockError
from src.simulation.output import OutputFormatter
from src.renderer.graphic_renderer import GraphicRenderer


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <map_file>")
        sys.exit(1)

    map_path = sys.argv[1]

    try:
        graph, nb_drones = MapParser.parse(map_path)

        drone_paths = Router.route(
            graph, graph.start_zone, graph.end_zone, nb_drones
        )

        engine = TurnEngine(graph, drone_paths)
        turns_log = engine.run()

        lines = OutputFormatter.format_turns(turns_log)
        for line in lines:
            print(line)

        renderer = GraphicRenderer(
            graph, turns_log, drone_image_path="assets/drone.png"
        )
        renderer.run()
    except ParseError as error:
        print(f"Error while parsing the map: {error}")
        sys.exit(1)
    except PathNotFoundError as error:
        print(f"Error while computing the route: {error}")
        sys.exit(1)
    except SimulationDeadlockError as error:
        print(f"Error while running the simulation: {error}")
        sys.exit(1)
    except Exception as error:
        print(f"Unexpected error: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
