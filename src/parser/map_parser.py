from .models import Graph
from typing import Optional


class ParseError(Exception):
    def __init__(self, line_number: int, message: str):
        print(f"Error on line {line_number}, {message}")


class MapParser:
    @staticmethod
    def parse(path: str) -> tuple[Graph, int]:
        graph = Graph()
        nb_drones: Optional[int] = None

        with open(path) as f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(":", 1)
                key = parts[0]
                value = parts[1]
                if key == "nb_drones":
                    nb_drones = MapParser._parse_nb_drones(value, line_number)
                elif key == "start_hub":
                    MapParser._parse_zone(value, graph, line_number, is_start=True)
                elif key == "end_hub":
                    MapParser._parse_zone(value, graph, line_number, is_end=True)
                elif key == "hub":
                    MapParser._parse_zone(value, graph, line_number)
                elif key == "connection":
                    MapParser._parse_connection(value, graph, line_number)
                else:
                    raise ParseError(line_number, "unknown prefix: ...")

        if nb_drones is None:
            raise ParseError(0, "nb_drones not defined")
        try:
            graph.start_zone
        except ValueError:
            raise ParseError(0, "start_hub not defined")
        try:
            graph.end_zone
        except ValueError:
            raise ParseError(0, "end_hub not defined")

        return (graph, nb_drones)
    

    @staticmethod
    def _parse_nb_drones(value: str, line_number: int) -> int:
        value = value.strip()
        try:
            value = int(value)
        except ValueError:
            raise ParseError(line_number, "nb_drones needs to be an intenger")
        if value <= 0:
            raise ParseError(line_number, "the value of nb_drones needs to be positive")
        return value


    @staticmethod
    def _parse_zone(value: str, graph: Graph,
                    line_number: int, is_start: bool = False, is_end: bool = False) -> None:
        value = value.strip()
        meta_data = value.split("[", 1)
        data = meta_data[0]
        data = data.strip()
        extra = meta_data[1]
        extra = extra.strip("]")
        name = data.split(" ", 1)[0]
        x = data.split(" ", 2)[1]
        y = data.split(" ", 2)[2]
        if not name or not x or not y:
            raise ParseError(line_number, "invalid zone")
        if " " in name or "-" in name:
            raise ParseError(line_number, "name cant have '-' or ' '")
        try:
            x = int(x)
            y = int(y)
        except ValueError:
            raise ParseError(line_number, "invalid coords")
        extra_parsed = MapParser._parse_meta_data(extra)
        types = ["normal", "blocked", "restricted", "priority"]
        if extra_parsed["zone"] not in types: