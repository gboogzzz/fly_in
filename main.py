from src.parser.map_parser import MapParser, ParseError
from src.pathfinding.router import Router
from src.pathfinding.dijkstra import PathNotFoundError
from src.simulation.engine import TurnEngine
from src.simulation.output import OutputFormatter
from src.renderer.graphic_renderer import GraphicRenderer


MAP_PATH = "maps/42maps/challenger/01_the_impossible_dream.txt"

def main() -> None:
    try:
        graph, nb_drones = MapParser.parse(MAP_PATH)

        drone_paths = Router.route(
          graph, graph.start_zone, graph.end_zone, nb_drones)

        engine = TurnEngine(graph, drone_paths)
        turns_log = engine.run()

        lines = OutputFormatter.format_turns(turns_log)
        for line in lines:
            print(line)

        renderer = GraphicRenderer(graph, turns_log, drone_image_path="assets/drone.png")
        renderer.run()
    except ParseError as error:
        print(f"Error while parsing the map: {error}")
    except PathNotFoundError as error:
        print(f"Error while computing the route: {error}")
    except Exception as error:
        print(f"Unexpected error: {error}")


if __name__ == "__main__":
    main()