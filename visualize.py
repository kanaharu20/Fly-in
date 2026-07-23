from parse import ProcessedData, Zone
import sys


class Visualizer:
    """Render the drone simulation to the terminal.

    When stdout is a TTY the output is colored and annotated (a zone
    legend plus a per-turn view).  When the output is piped or
    redirected it falls back to the plain, machine-readable format
    required by the subject (one line per turn, ``D<id>-<zone>``
    tokens separated by spaces).
    """

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    COLOR_CODES: dict[str, str] = {
        "black": "\033[30m",
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "purple": "\033[35m",
        "cyan": "\033[36m",
        "white": "\033[37m",
        "gray": "\033[90m",
        "grey": "\033[90m",
        "orange": "\033[38;5;208m",
    }

    def __init__(
        self, data: ProcessedData, use_color: bool | None = None
    ) -> None:
        self._data = data
        if use_color is None:
            use_color = sys.stdout.isatty()
        self._use_color = use_color
        self._color_of: dict[str, str] = {
            zone.get_name(): zone.get_color()
            for zone in self._all_zones()
        }

    def _all_zones(self) -> list[Zone]:
        zones: list[Zone] = list(self._data._zone_dict.values())
        zones.append(self._data._start_hub)
        zones.append(self._data._end_hub)
        return zones

    def _paint(self, text: str, color: str) -> str:
        if not self._use_color:
            return text
        code = self.COLOR_CODES.get(color.lower())
        if code is None:
            return text
        return f"{code}{text}{self.RESET}"

    def _wrap(self, text: str, code: str) -> str:
        if not self._use_color:
            return text
        return f"{code}{text}{self.RESET}"

    def render_legend(self) -> None:
        start = self._data._start_hub.get_name()
        end = self._data._end_hub.get_name()
        print("Zones:")
        for zone in self._all_zones():
            name = zone.get_name()
            swatch = self._paint("*", zone.get_color())
            role = "start" if name == start else (
                "end" if name == end else zone.get_zone_type().value
            )
            cap = "inf" if name in (start, end) else str(
                zone.get_max_drones()
            )
            print(f"  {swatch} {name} ({role}, capacity={cap})")

    def _render_line(self, turn_no: int, line: str) -> str:
        tokens = line.split(" ") if line else []
        painted: list[str] = []
        for tok in tokens:
            head, sep, rest = tok.partition("-")
            head = self._wrap(head, self.BOLD)
            if rest in self._color_of:
                rest = self._paint(rest, self._color_of[rest])
            else:
                # In flight toward a restricted zone (a connection name).
                rest = self._wrap(rest, self.DIM)
            painted.append(f"{head}{sep}{rest}")
        return f"Turn {turn_no:>3}: " + " ".join(painted)

    def render(self, move_log: list[str]) -> None:
        # When piped/redirected, output_log already printed the plain
        # spec-format log; stay silent so that output is not doubled.
        if not self._use_color:
            return
        print()
        print(self._wrap("=== Visualization ===", self.BOLD))
        self.render_legend()
        print()
        for turn_no, line in enumerate(move_log, start=1):
            print(self._render_line(turn_no, line))
        print()
        drone_num = len(self._data._drone_dict)
        turns = len(move_log)
        moves = sum(len(line.split(" ")) for line in move_log if line)
        print(f"Drones: {drone_num}")
        print(f"Total turns (score): {turns}")
        if turns:
            print(f"Average moves per turn: {moves / turns:.2f}")
