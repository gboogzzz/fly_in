*This project has been created as part of the 42 curriculum by gguia-ma.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start zone to an end zone through a
network of zones and connections, in as few simulation turns as possible.

The map is read from a text file. Zones have a type (`normal`, `priority`,
`restricted` or `blocked`) and a capacity (`max_drones`), and connections have
a capacity (`max_link_capacity`). The program computes a path for every
drone, simulates the movement turn by turn without breaking any capacity
limit, prints the movements and can show them in a graphical window.

Movement costs: entering a `normal` or `priority` zone takes 1 turn, entering
a `restricted` zone takes 2 turns, and `blocked` zones cannot be used.

## Instructions

Requirements: Python 3.10 or later.

```
make install                 # creates .venv and installs requirements.txt
make run MAP=maps/map.txt    # runs the simulation (python3 -m src.main)
make debug MAP=maps/map.txt  # runs it with pdb
make lint                    # flake8 + mypy
make lint-strict             # flake8 + mypy --strict
make clean                   # removes __pycache__ and .mypy_cache
```

The program prints the movements and then opens the graphical viewer.
Viewer keys: `SPACE` or `→` next turn, `←` previous turn, `ESC` or `Q` quit.
It also advances on its own every 1.5 seconds.

### Map format

```
nb_drones: 5
start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
connection: hub-corridorA
connection: corridorA-goal [max_link_capacity=2]
```

Any error in the file stops the program with a message in the form
`Error on line N: <cause>`.

## Algorithm and implementation strategy

1. **Parsing** (`parser`): `MapParser` validates the file and builds a
   `Graph`, an undirected graph stored as an adjacency list. Blocked zones are
   never added as neighbours.
2. **Shortest path** (`pathfinding/dijkstra.py`): Dijkstra with a binary heap,
   O((V + E) log V). The cost of a path is the pair `(turns, priority bonus)`,
   compared in order. Fewer turns always win, and when two paths take the same
   number of turns the one through more `priority` zones is chosen.
3. **Several paths** (`pathfinding/k_paths.py`): Yen's algorithm finds the K
   cheapest loopless paths, so drones can be spread over different routes.
   About O(K · V · (V + E) log V).
4. **Distribution** (`pathfinding/router.py`): the capacity of a path is the
   minimum of the `max_drones` of its intermediate zones and the
   `max_link_capacity` of its connections. K grows until the summed capacity
   fits all drones, and the drones are split across the paths in proportion
   to their capacity.
5. **Simulation** (`simulation`): `TurnEngine` moves the drones one turn at a
   time. `Scheduler` keeps the zone occupancy and the connection usage per
   turn, so a drone waits when the next zone or connection is full. Moving
   into a `restricted` zone reserves the connection for both turns and the
   destination zone from the start, since the drone cannot stop in the middle
   of the connection. If nobody can move and nobody is in transit, a
   deadlock error is raised.
6. **Output** (`simulation/output.py`): one line per turn, with the moves of
   that turn sorted by drone id.

Known limitation: drones are assigned to paths by capacity only, without
considering the path length, so it does not always reach the minimum number
of turns.

## Visual representation

`GraphicRenderer` (pygame) draws the network and the drones:

- Zones are circles coloured by their `color` metadata, or by their type when
  there is none. Connections are lines and zone names are shown below.
- Drones move smoothly between turns. A drone flying to a `restricted` zone is
  drawn halfway along the connection, which makes the 2-turn cost visible.
- Stepping forward and backward through the turns makes it easy to see where
  drones wait and where the bottlenecks are.
- If `assets/drone.png` is missing, drones are drawn as labelled circles.

## Example

Input (`maps/example.txt`):

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

Output (6 turns):

```
D1-corridorA D4-hub-roof1
D1-tunnelB D2-corridorA D4-roof1
D1-goal D2-tunnelB D3-corridorA D4-roof2 D5-hub-roof1
D2-goal D3-tunnelB D4-goal D5-roof1
D3-goal D5-roof2
D5-goal
```

`D4-hub-roof1` is a drone still in flight toward the restricted zone `roof1`.

## Resources

- Dijkstra's algorithm: https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm
- Yen's algorithm (K shortest paths): https://en.wikipedia.org/wiki/Yen%27s_algorithm

### Use of AI

AI was used only to explain concepts as they were asked about during development.