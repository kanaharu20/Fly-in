from parse import ProcessedData, Zone, ZoneTypes, Drone, Connection
import heapq
from enum import Enum


class Action(Enum):
    ZONE = 1
    INBETWEEN = 2
    STOP = 3


class MoveDrone:
    def __init__(self, data: ProcessedData):
        self._move_log: list[str] = []
        self._data: ProcessedData = data

    def _get_zone(self, name: str) -> Zone:
        if name == self._data._start_hub.name:
            return self._data._start_hub
        if name == self._data._end_hub.name:
            return self._data._end_hub
        return self._data._zone_dict[name]

    def build_candi_dict(self) -> dict[str, list[str]]:
        all_zones = list(self._data._zone_dict.values())
        all_zones.append(self._data._start_hub)
        all_zones.append(self._data._end_hub)

        candi_dict: dict[str, list[str]] = {}
        for zone in all_zones:
            if zone.zone_type == ZoneTypes.BLOCKED:
                continue
            candis: list[str] = []
            for key in self._data._connection_dict.keys():
                if zone.name in key and all(
                    self._get_zone(name).zone_type != ZoneTypes.BLOCKED
                    for name in key
                        ):
                    candis.append(next(
                        name for name in key if name != zone.name
                        ))
            candi_dict[zone.name] = candis
        return candi_dict

    def cost_of(self, name: str) -> int:
        zone = self._get_zone(name)
        return 2 if zone.zone_type == ZoneTypes.RESTRICTED else 1

    def dijkstra(
            self, start: str, candi_dict: dict[str, list[str]]
            ) -> dict[str, int]:
        dist: dict[str, int] = {start: 0}
        queue: list[tuple[int, str]] = [(0, start)]

        while queue:
            current_cost, current_zone = heapq.heappop(queue)
            if current_cost > dist.get(current_zone, float("inf")):
                continue

            for neighbor in candi_dict[current_zone]:
                new_cost = current_cost + self.cost_of(neighbor)
                if new_cost < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor))

        return dist

    def build_cost_table(self) -> dict[str, int]:
        goal_name = self._data._end_hub.name
        candi_dict = self.build_candi_dict()
        raw_dist = self.dijkstra(goal_name, candi_dict)

        goal_cost = self.cost_of(goal_name)
        return {
            name: dist + goal_cost - self.cost_of(name)
            for name, dist in raw_dist.items()
        }

    def is_accessible(self, current: Zone, next: Zone) -> bool:
        if next.get_max_drones < 1:
            return False
        connection = self._data._connection_dict[
            frozenset(current.name, next.name)
            ]
        if connection.get_capa() < 1:
            return False
        return True

    def select_zone(self, zone: str) -> str:
        neighbours = self.build_candi_dict()[zone]
        cost_table = self.build_cost_table()

        min_cost = min(list(cost_table[name] for name in neighbours))

        for name in neighbours:
            if (
                (cost_table[name] == min_cost) and
                    (self._get_zone(name).get_zone_type == ZoneTypes.PRIORITY)
                    ):
                if self.is_accessible(
                    self._get_zone(zone), self._get_zone(name)
                ):
                    return name
        for name in neighbours:
            if cost_table[name] == min_cost:
                if self.is_accessible(
                    self._get_zone(zone), self._get_zone(name)
                ):
                    return name
        return None

    def in_connection(self, drone: Drone, zone: Zone) -> None:
        drone.set_connection_to(zone)
        connection = self._data._connection_dict[
            frozenset(drone.get_zone(), zone)
            ]
        connection.reduce_capa()

    def out_connection(self, drone: Drone) -> None:
        connection: Connection = self._data[
            frozenset(drone.get_zone(), drone.get_connection_to())
        ]
        drone.zone = drone.get_connection_to()
        drone.set_connection_to(None)
        connection.increase_capa()

    def move_to_zone(self, drone: Drone, zone: Zone) -> None:
        drone.update_zone(zone)
        zone.reduce_max_drones()

    def start_algo(self) -> None:
        finished: list[int] = []
        drone_num: int = len(self._data._drone_dict)
        while len(finished) != drone_num:
            changed: list[int] = []
            for i in range(drone_num):
                drone: Drone = self._data._drone_dict[i]
                if drone.connection_to is not None:
                    self.out_connection(drone)
                    changed.append(i)
                    continue
                next_hub: Zone = self.select_zone(drone.get_zone())
                if next_hub is None:
                    continue
                if next_hub.get_zone_type() == ZoneTypes.RESTRICTED:
                    self.in_connection(drone, next_hub)
                self.move_to_zone(drone, next_hub)
                changed.append(drone)
            log_line: str = " ".join(changed)
            self._move_log.append(log_line)

    def output_log(self) -> None:
        for line in self._move_log:
            print(line)


def run():
    movedrone: MoveDrone = MoveDrone()
    movedrone.start_algo()
    movedrone.output_log()
