"""Map file parser for the Fly-in drone routing simulation.

Reads a map file and builds the corresponding Graph and the number of
drones. Every error found while parsing is reported as a ParseError that
contains the line number and the cause.
"""

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
    """Raised when the map file is invalid.

    The message always follows the format ``Error on line N: <cause>``.
    Errors that do not belong to a specific line (e.g. a missing
    ``start_hub`` or an unreadable file) use line number 0.
    """

    def __init__(self, line_number: int, message: str):
        """Build the error with the line number and the cause.

        Args:
            line_number: Line of the map file where the error was found,
                or 0 if it does not belong to a specific line.
            message: Description of the cause of the error.
        """
        super().__init__(f"Error on line {line_number}: {message}")


class MapParser:
    """Parser that converts a map file into a Graph.

    All methods are static because the parser keeps no state between
    calls: the graph and the number of drones are local to each parse.
    """

    @staticmethod
    def parse(path: str) -> tuple[Graph, int]:
        """Parse a map file.

        The file is read line by line. Empty lines and comments (lines
        starting with ``#``) are ignored. The first meaningful line must
        define ``nb_drones``, and there must be exactly one ``start_hub``
        and one ``end_hub``.

        Args:
            path: Path to the map file.

        Returns:
            A tuple with the built graph and the number of drones.

        Raises:
            ParseError: If the file cannot be opened, or if any line or
                the overall structure of the file is invalid.
        """
        graph = Graph()
        nb_drones: Optional[int] = None
        has_start = False
        has_end = False

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

                if key != "nb_drones" and nb_drones is None:
                    raise ParseError(
                        line_number,
                        "the first line must define 'nb_drones'",
                    )

                if key == "nb_drones":
                    if nb_drones is not None:
                        raise ParseError(
                            line_number, "nb_drones defined more than once"
                        )
                    nb_drones = MapParser._parse_nb_drones(
                        value, line_number
                    )
                elif key == "start_hub":
                    if has_start:
                        raise ParseError(
                            line_number, "start_hub defined more than once"
                        )
                    has_start = True
                    MapParser._parse_zone(
                        value, graph, line_number, is_start=True
                    )
                elif key == "end_hub":
                    if has_end:
                        raise ParseError(
                            line_number, "end_hub defined more than once"
                        )
                    has_end = True
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
        if not has_start:
            raise ParseError(0, "start_hub not defined")
        if not has_end:
            raise ParseError(0, "end_hub not defined")

        return (graph, nb_drones)

    @staticmethod
    def _parse_nb_drones(value: str, line_number: int) -> int:
        """Parse the value of the ``nb_drones`` line.

        Args:
            value: Text after ``nb_drones:``.
            line_number: Line number, used in error messages.

        Returns:
            The number of drones.

        Raises:
            ParseError: If the value is not an integer or is not positive.
        """
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
        """Parse a zone line and add the zone to the graph.

        The expected format is ``<name> <x> <y> [metadata]``, where the
        metadata block is optional and may contain ``zone``, ``color``
        and ``max_drones``. The name, x and y are split on single spaces.

        Args:
            value: Text after ``hub:``, ``start_hub:`` or ``end_hub:``.
            graph: Graph where the zone is added.
            line_number: Line number, used in error messages.
            is_start: True if the zone is the start zone.
            is_end: True if the zone is the end zone.

        Raises:
            ParseError: If the format, the coordinates, the metadata, the
                zone type or the capacity are invalid, or if a zone with
                the same name already exists.
        """
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
            extra_parsed = MapParser._parse_meta_data(
                extra, line_number, {"zone", "color", "max_drones"}
            )
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
        try:
            zone_type = ZoneType(zone_type_str)
        except ValueError:
            raise ParseError(
                line_number, f"invalid zone type '{zone_type_str}'"
            )

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
        """Parse a connection line and add the connection to the graph.

        The expected format is ``<zone1>-<zone2> [metadata]``, where the
        metadata block is optional and may contain ``max_link_capacity``.
        Both zones must have been defined on previous lines.

        Args:
            value: Text after ``connection:``.
            graph: Graph where the connection is added.
            line_number: Line number, used in error messages.

        Raises:
            ParseError: If the format or the metadata are invalid, if a
                zone is unknown, if the capacity is not a positive
                integer, if the zone is connected to itself, or if the
                connection is a duplicate (in either direction).
        """
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
            raise ParseError(line_number, f"unknown zone '{name1}'")
        try:
            zone2 = graph.get_zone(name2)
        except ZoneNotFoundError:
            raise ParseError(line_number, f"unknown zone '{name2}'")

        if extra:
            extra_parsed = MapParser._parse_meta_data(
                extra, line_number, {"max_link_capacity"}
            )
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

        try:
            connection = Connection(zone1, zone2, max_link_capacity)
        except ValueError as e:
            raise ParseError(line_number, str(e))

        try:
            graph.add_connection(connection)
        except DuplicateConnectionError:
            raise ParseError(line_number, "cant have duplicate connections")
        except ValueError:
            raise ParseError(
                line_number, "one of the zones weren't added to the graph"
            )

    @staticmethod
    def _parse_meta_data(
        metadata_str: str, line_number: int, allowed: set[str]
    ) -> dict[str, str]:
        """Parse a metadata block into a dictionary.

        Converts text such as ``zone=restricted color=red]`` into
        ``{"zone": "restricted", "color": "red"}``. Values are returned
        as strings and must be converted by the caller.

        Args:
            metadata_str: Text of the metadata block, after the ``[``.
            line_number: Line number, used in error messages.
            allowed: Set of metadata keys accepted in this context.

        Returns:
            Dictionary mapping each metadata key to its value.

        Raises:
            ParseError: If a tag has no ``=``, if a key is not in
                ``allowed``, or if a key appears more than once.
        """
        metadata_str = metadata_str.strip("[]")
        meta_data = metadata_str.split()
        parsed_data: dict[str, str] = {}
        for data in meta_data:
            temp = data.split("=", 1)
            if len(temp) < 2:
                raise ParseError(line_number, "mal formed meta data")
            key, value = temp
            if key not in allowed:
                raise ParseError(
                    line_number,
                    f"unknown metadata '{key}' "
                    f"(allowed: {', '.join(sorted(allowed))})",
                )
            if key in parsed_data:
                raise ParseError(line_number, f"duplicate metadata '{key}'")
            parsed_data[key] = value

        return parsed_data
