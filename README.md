*This project has been created as part of the 42 curriculum by hkanamit.*

# Fly-in

## Description

Fly-in is a drone routing simulator. Given a map that describes a network
of **zones** (nodes) connected by bidirectional **connections** (edges), the
program routes a fleet of drones from a single `start_hub` to a single
`end_hub` in as few simulation turns as possible, while respecting movement
costs and capacity constraints.

Zones have a **type** that affects movement:

| Type         | Movement cost | Notes                                   |
| ------------ | ------------- | --------------------------------------- |
| `normal`     | 1 turn        | Default.                                |
| `priority`   | 1 turn        | Preferred during pathfinding.           |
| `restricted` | 2 turns       | The drone spends one turn on the        |
|              |               | connection, then arrives the next turn. |
| `blocked`    | —             | Impassable; never entered.              |

Capacities limit how many drones may share a zone (`max_drones`, default 1)
or traverse a connection at once (`max_link_capacity`, default 1). The
`start_hub` and `end_hub` are unlimited.

## Instructions

The project targets **Python 3.10+** and is managed with
[`uv`](https://docs.astral.sh/uv/). A `Makefile` wraps the common tasks:

```sh
make install          # install dependencies (uv sync)
make run              # run on the default map (maps/easy/01_linear_path.txt)
make run MAP=maps/hard/03_ultimate_challenge.txt   # run on a chosen map
make debug            # run under pdb
make lint             # flake8 . + mypy (mandatory flags)
make lint-strict      # flake8 . + mypy --strict
make clean            # remove __pycache__ / .mypy_cache
```

You can also run it directly:

```sh
python main.py <map_file>
```

When the output is a terminal, a colored visualization is shown in addition
to the plain log. When the output is piped or redirected, only the plain,
spec-compliant log is produced (so it stays easy to parse).

## Example input and expected output

Input (`maps/easy/01_linear_path.txt`):

```
# Easy Level 1: Simple linear path
nb_drones: 2

start_hub: start 0 0 [color=green]
hub: waypoint1 1 0 [color=blue]
hub: waypoint2 2 0 [color=blue]
end_hub: goal 3 0 [color=red]

connection: start-waypoint1
connection: waypoint1-waypoint2
connection: waypoint2-goal
```

Expected output (plain log):

```
D0-waypoint1
D0-waypoint2 D1-waypoint1
D0-goal D1-waypoint2
D1-goal
Score: 4 turns
```

Each line is one simulation turn and lists the movements that happened,
space-separated. A movement is `D<id>-<zone>`, or `D<id>-<connection>` while
a drone is still in flight toward a `restricted` zone.

## Algorithm and implementation strategy

The project is split into three object-oriented modules.

### Parsing (`parse.py`)

Parsing uses a small **Strategy** pattern. Each kind of line has a processor
(`DroneNumProcesser`, `HubProcesser`, `ConnectionProcesser`) that implements
`validate` and `ingest`. A `DataStream` feeds every non-comment line to the
first processor that accepts it, and raises a clear error (with line number
and cause) otherwise. The validated data is materialised into typed
[pydantic](https://docs.pydantic.dev/) models — `Zone`, `Connection`,
`Drone` — held by `ProcessedData`. Validation covers duplicate names and
coordinates, unknown zone types, malformed metadata, unknown connection
endpoints, and duplicate connections (`a-b` equals `b-a`).

### Pathfinding (`algorithm.py`)

1. **Cost table.** A single-source **Dijkstra from the goal** computes the
   cost-to-reach-the-goal for every zone, using the zone-type movement costs
   (`restricted` = 2, everything else = 1) and skipping `blocked` zones.
   Unreachable goals and isolated zones are detected here and reported.
2. **Turn-by-turn scheduling.** Each turn, every not-yet-delivered drone
   (in id order) either finishes an in-flight `restricted` move, or greedily
   steps to the accessible neighbor with the lowest cost-to-goal, preferring
   `priority` zones on ties.
3. **Capacity handling.** Zone `max_drones` and connection
   `max_link_capacity` are tracked as live counters. Connection capacity is
   reserved for the duration of a turn and released afterward; a
   `restricted` destination reserves its slot on *entry* so two drones cannot
   force an over-capacity arrival on the same turn.

Because all drones share a single goal and only ever move toward it, the
scheduler always advances the drone nearest the goal, so it makes progress
every turn on any connected map.

### Visual representation (`visualize.py`)

The `Visualizer` renders the run to the terminal. When stdout is a TTY it
prints:

- a **zone legend** — each zone with a colored swatch (from its `color=`
  metadata), its role/type, and its capacity, giving an at-a-glance view of
  the network's state;
- the **per-turn movements**, with each destination zone colored by its
  zone color and drones in flight dimmed;
- **secondary metrics** (drone count, total turns/score, average moves per
  turn) to help peers compare performance.

When stdout is not a TTY the visualizer stays silent and only the plain
spec-format log (from `output_log`) is emitted, so redirected output remains
machine-readable.

## Performance

All provided maps meet the subject's reference targets:

| Map                             | Turns | Target |
| ------------------------------- | ----- | ------ |
| easy/linear_path                | 4     | <= 6   |
| easy/simple_fork                | 4     | <= 8   |
| easy/basic_capacity             | 4     | <= 6   |
| medium/dead_end_trap            | 8     | <= 12  |
| medium/circular_loop            | 15    | <= 15  |
| medium/priority_puzzle          | 7     | <= 12  |
| hard/maze_nightmare             | 13    | <= 30  |
| hard/capacity_hell              | 16    | <= 35  |
| hard/ultimate_challenge         | 26    | <= 45  |
| challenger/the_impossible_dream | 45    | 45     |

## Resources

- Dijkstra's shortest path algorithm — for the cost-to-goal table.
- 42's `lem-in` project — classic inspiration for turn-based multi-agent
  routing on a graph.
- [pydantic documentation](https://docs.pydantic.dev/) — typed, validated
  data models.
- [mypy](https://mypy.readthedocs.io/) and
  [flake8](https://flake8.pycqa.org/) — static type checking and style.
- ANSI escape codes — for the colored terminal output.

### Use of AI

AI (Claude Code) was used to review the codebase against the subject and to
assist with: fixing type-safety issues so the project passes `mypy`,
correcting parser behavior (accepting hubs without optional metadata),
fixing a zone-capacity bug affecting `restricted` zones, and implementing
the colored terminal visualization. All AI-suggested changes were reviewed
and are understood by the author.