from parse import ProcessedData, Zone, ZoneTypes
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
                    candis.append(next(name for name in key if name != zone.name))
            candi_dict[zone.name] = candis
        return candi_dict

    def cost_of(self, name: str) -> int:
        zone = self._get_zone(name)
        return 2 if zone.zone_type == ZoneTypes.RESTRICTED else 1

    def dijkstra(self, start: str, candi_dict: dict[str, list[str]]) -> dict[str, int]:
        dist: dict[str, int] = {start: 0}
        queue: list[tuple[int, str]] = [(0, start)]

        while queue:
            current_cost, current_zone = heapq.heappop(queue)
            if current_cost > dist.get(current_zone, float("inf")):
                continue  # 他の経路で既にもっと安く確定済み

            for neighbor in candi_dict[current_zone]:
                new_cost = current_cost + self.cost_of(neighbor)
                if new_cost < dist.get(neighbor, float("inf")):
                    dist[neighbor] = new_cost
                    heapq.heappush(queue, (new_cost, neighbor))

        return dist

    def build_dist_table(self) -> dict[str, int]:
        goal_name = self._data._end_hub.name
        candi_dict = self.build_candi_dict()
        raw_dist = self.dijkstra(goal_name, candi_dict)

        # raw_distはgoal基準の距離。あるゾーンに実際に立っているドローンが
        # goalまでに使うターン数は、そのゾーン自身に入るコストは払わなくていい分
        # ズレるので、goal自身のコストを足して自分のコストを引いて補正する。
        goal_cost = self.cost_of(goal_name)
        return {
            name: dist + goal_cost - self.cost_of(name)
            for name, dist in raw_dist.items()
        }
