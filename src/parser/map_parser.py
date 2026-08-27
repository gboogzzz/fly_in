from typing import Optional
from ..models import (
    Graph,
    Zone,
    Connection,
    ZoneNotFoundError,
    DuplicateConnectionError,
    ZoneType,
)


class ParseError(Exception):
    def __init__(self, line_number: int, message: str):
        super().__init__(f"Error on line {line_number}: {message}")


class MapParser:
    @staticmethod
    def parse(path: str) -> tuple[Graph, int]:
        graph = Graph()
        nb_drones: Optional[int] = None

        try:
            f = open(path)
        except OSError as e:
            raise ParseError(0, f"could not open file '{path}': {e}")

        with f:
            for line_number, line in enumerate(f, start=1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                parts = line.split(":", 1)
                if len(parts) != 2:
                    raise ParseError(
                        line_number, f"missing ':' separator in '{line}'"
                    )
                key, value = parts
                key = key.strip()

                if key == "nb_drones":
                    nb_drones = MapParser._parse_nb_drones(
                        value, line_number
                    )
                elif key == "start_hub":
                    MapParser._parse_zone(
                        value, graph, line_number, is_start=True
                    )
                elif key == "end_hub":
                    MapParser._parse_zone(
                        value, graph, line_number, is_end=True
                    )
                elif key == "hub":
                    MapParser._parse_zone(value, graph, line_number)
                elif key == "connection":
                    MapParser._parse_connection(value, graph, line_number)
                else:
                    raise ParseError(line_number, f"unknown prefix: '{key}'")

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
            nb_drones = int(value)
        except ValueError:
            raise ParseError(
                line_number, "nb_drones needs to be an integer"
            )
        if nb_drones <= 0:
            raise ParseError(
                line_number, "the value of nb_drones needs to be positive"
            )
        return nb_drones

    @staticmethod
    def _parse_zone(
        value: str,
        graph: Graph,
        line_number: int,
        is_start: bool = False,
        is_end: bool = False,
    ) -> None:
        value = value.strip()
        color = None
        max_drones = 1
        extra: Optional[str] = None
        extra_parsed: dict[str, str] = {}

        if "[" in value:
            meta_data = value.split("[", 1)
            data = meta_data[0].strip()
            extra = meta_data[1]
            if not extra.endswith("]"):
                raise ParseError(line_number, "missing closing ']'")
            tokens = data.split(" ", 2)
        else:
            tokens = value.split(" ", 2)

        if len(tokens) < 3:
            raise ParseError(line_number, "expected '<name> <x> <y>'")
        name, x_str, y_str = tokens

        if not name or not x_str or not y_str:
            raise ParseError(line_number, "invalid zone")
        if "-" in name:
            raise ParseError(line_number, "name cant have '-' or ' '")

        try:
            x = int(x_str)
            y = int(y_str)
        except ValueError:
            raise ParseError(line_number, "invalid coords")

        if extra:
            extra_parsed = MapParser._parse_meta_data(extra, line_number)
            types = ["normal", "blocked", "restricted", "priority"]
            if extra_parsed.get("zone", "normal") not in types:
                raise ParseError(line_number, "zone_type invalid")
            color = extra_parsed.get("color")
            try:
                max_drones = int(extra_parsed.get("max_drones", "1"))
            except ValueError:
                raise ParseError(
                    line_number, "max_drones needs to be an integer"
                )
            if max_drones <= 0:
                raise ParseError(
                    line_number, "max_drones must be positive"
                )

        zone_type_str = extra_parsed.get("zone", "normal")
        zone_type = ZoneType.from_string(zone_type_str)

        try:
            zone = Zone(
                name, x, y, zone_type, max_drones, color, is_start, is_end
            )
        except ValueError as e:
            raise ParseError(line_number, str(e))

        try:
            graph.add_zone(zone)
        except ValueError:
            raise ParseError(line_number, "zone already exist")

    @staticmethod
    def _parse_connection(value: str, graph: Graph, line_number: int) -> None:
        value = value.strip()
        max_link_capacity = 1
        extra: Optional[str] = None

        if "[" in value:
            meta_data = value.split("[", 1)
            data = meta_data[0].strip()
            extra = meta_data[1]
            if not extra.endswith("]"):
                raise ParseError(line_number, "missing closing ']'")
        else:
            data = value

        parts = data.split("-")
        if len(parts) != 2:
            raise ParseError(line_number, "expected '<zone1>-<zone2>'")
        name1, name2 = parts

        if not name1 or not name2:
            raise ParseError(line_number, "mal formed zone")

        try:
            zone1 = graph.get_zone(name1)
        except ZoneNotFoundError:
            raise ParseError(line_number, "unknown zone")
        try:
            zone2 = graph.get_zone(name2)
        except ZoneNotFoundError:
            raise ParseError(line_number, "unknown zone")

        if extra:
            extra_parsed = MapParser._parse_meta_data(extra, line_number)
            try:
                max_link_capacity = int(
                    extra_parsed.get("max_link_capacity", "1")
                )
            except ValueError:
                raise ParseError(
                    line_number, "max_link_capacity needs to be an integer"
                )
            if max_link_capacity <= 0:
                raise ParseError(
                    line_number,
                    "max_link_capacity needs to be a positive integer",
                )

        connection = Connection(zone1, zone2, max_link_capacity)
        try:
            graph.add_connection(connection)
        except ValueError:
            raise ParseError(
                line_number, "one of the zones weren't added to the graph"
            )
        except DuplicateConnectionError:
            raise ParseError(line_number, "cant have duplicate connections")

    @staticmethod
    def _parse_meta_data(
        metadata_str: str, line_number: int
    ) -> dict[str, str]:
        metadata_str = metadata_str.strip("[]")
        meta_data = metadata_str.split(" ")
        parsed_data = {}
        for data in meta_data:
            temp = data.split("=", 1)
            if len(temp) < 2:
                raise ParseError(line_number, "mal formed meta data")
            key = temp[0]
            parsed_data[key] = temp[1]

        return parsed_data