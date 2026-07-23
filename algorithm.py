from parse import ProcessedData, Zone, ZoneTypes, Drone, Connection
import heapq


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

    def _is_hub(self, zone: Zone) -> bool:
        return zone.name in (
            self._data._start_hub.name, self._data._end_hub.name
            )

    def is_accessible(self, current: Zone, next: Zone) -> bool:
        if not self._is_hub(next) and next.get_max_drones() < 1:
            return False
        connection = self._data._connection_dict[
            frozenset([current.name, next.name])
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
                    (self._get_zone(name).get_zone_type() == ZoneTypes.PRIORITY)
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
        old_zone: Zone = drone.get_zone()
        drone.set_connection_to(zone)
        connection = self._data._connection_dict[
            frozenset([old_zone.name, zone.name])
            ]
        connection.reduce_capa()
        if not self._is_hub(old_zone):
            old_zone.increase_max_drones()

    def out_connection(self, drone: Drone) -> None:
        next_zone: Zone = drone.get_connection_to()
        connection: Connection = self._data._connection_dict[
            frozenset([drone.get_zone().name, next_zone.name])
        ]
        drone.zone = next_zone
        drone.set_connection_to(None)
        connection.increase_capa()
        if not self._is_hub(next_zone):
            next_zone.reduce_max_drones()

    def move_to_zone(self, drone: Drone, zone: Zone) -> None:
        old_zone: Zone = drone.get_zone()
        drone.update_zone(zone)
        if not self._is_hub(zone):
            zone.reduce_max_drones()
        if not self._is_hub(old_zone):
            old_zone.increase_max_drones()

    def write_log_line(self, changed: list[int]) -> str:
        contains: list[str] = []
        for id_num in changed:
            drone: Drone = self._data._drone_dict[id_num]
            if drone.connection_to is not None:
                connection: Connection = self._data._connection_dict[
                    frozenset([drone.get_connection_to().name,
                               drone.get_zone().name])].get_name()
                tmp: str = f"D{id_num}-{connection}"
                contains.append(tmp)
            else:
                hub: str = drone.get_zone().get_name()
                tmp = f"D{id_num}-{hub}"
                contains.append(tmp)
        return " ".join(contains)

    def start_algo(self) -> None:
        finished: list[int] = []
        drone_num: int = len(self._data._drone_dict)
        while len(finished) != drone_num:
            changed: list[int] = []
            for i in range(drone_num):
                if i in finished:
                    continue
                drone: Drone = self._data._drone_dict[i]
                if drone.connection_to is not None:
                    self.out_connection(drone)
                    changed.append(i)
                    if drone.get_zone() == self._data._end_hub:
                        finished.append(drone.get_id())
                    continue
                next_hub_name: str = self.select_zone(drone.get_zone().name)
                if next_hub_name is None:
                    continue
                next_hub: Zone = self._get_zone(next_hub_name)
                if next_hub.get_zone_type() == ZoneTypes.RESTRICTED:
                    self.in_connection(drone, next_hub)
                else:
                    self.move_to_zone(drone, next_hub)
                    if drone.get_zone() == self._data._end_hub:
                        finished.append(drone.get_id())
                changed.append(i)
            log_line: str = self.write_log_line(changed)
            self._move_log.append(log_line)

    def output_log(self) -> None:
        for line in self._move_log:
            print(line)


def run():
    movedrone: MoveDrone = MoveDrone()
    movedrone.start_algo()
    movedrone.output_log()
