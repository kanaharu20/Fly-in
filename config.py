from pydantic import BaseModel, model_validator, Field
from enum import Enum
from abc import ABC, abstractmethod
import re


class ZoneTypes(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Drone(BaseModel):
    id: int = Field(ge=0)
    xy: tuple[int, int]

    def set_id(self, num: int) -> None:
        self.id = num

    def update_coodinate(self, xy: tuple[int, int]) -> None:
        self.xy = xy

    def reach_goal(self) -> None:
        self.at_goal = True


class Zone(BaseModel):
    name: str
    xy: tuple[int, int]
    color: str
    max_drones: int = Field(default=1, ge=1)
    zone_type: ZoneTypes

    @model_validator(mode="after")
    def zone_validate(self) -> "Zone":
        if any([' ' in self.name, '-' in self.name]):
            raise ValueError(
                "Zone names can use any valid "
                "characters except dashes and spaces."
            )
        return self


class Connection(BaseModel):
    name: set
    capacity: int = Field(default=1, ge=1)


class ProcessedData:
    def __init__(self) -> None:
        self._zone_dict: dict[str, Zone] = {}
        self._connection_dict: dict[set, Connection] = {}
        self._zone_name_list: list[str] = []

    def append_zone(self, data: list[tuple]) -> None:
        for line in data:
            tmp: list[str] = list(x for x in re.split(
                r"[: ]", line[1].strip()) if x
                    )[1:]
            xy: tuple[int, int] = int(tmp[1]), int(tmp[2])
            color: str = ""
            max_drones: int = 1
            zone_type: ZoneTypes = ZoneTypes.NORMAL
            if len(tmp) > 3:
                bracket: str = " ".join(tmp[3:])
                meta_data: list[str] = bracket.strip("[]").split(" ")
                for data in meta_data:
                    if "color" in data:
                        color = data.split("=")[1]
                    if "max_drones" in data:
                        max_drones = int(data.split("=")[1])
                    if "zone" in data:
                        type_name = data.split("=")[1].strip()
                        if type_name == "restricted":
                            zone_type = ZoneTypes.RESTRICTED
                        elif type_name == "priority":
                            zone_type = ZoneTypes.PRIORITY
                        elif type_name == "blocked":
                            zone_type = ZoneTypes.BLOCKED
                        else:
                            raise ValueError
            zone: Zone = Zone(
                name=tmp[0], xy=xy, color=color,
                max_drones=max_drones, zone_type=zone_type
                )
            self._zone_dict[tmp[0]] = zone
            self._zone_name_list.append(tmp[0])

    def append_connection(self, data: list[tuple]) -> None:
        zone_name_list: list[str] = []
        for zone in self._zone_dict.values():
            zone_name_list.append(zone.name)
        for line in data:
            tmp: list[str] = list(x for x in re.split(
                r"[ :]", line[1].strip()) if x
                )[1:]
            zone_names = tmp[0].split("-")
            for name in zone_names:
                if name not in zone_name_list:
                    raise ValueError(f"{name} is not found in hub names.")
            name_set = frozenset(zone_names)
            max_link_capa: int = 1
            if len(tmp) > 1:
                max_link_capa = int(tmp[1].strip("[]").split("=")[1])
            connection: Connection = Connection(
                name=name_set, capacity=max_link_capa
            )
            self._connection_dict[name_set] = connection


class DataProcesser(ABC):
    def __init__(self) -> None:
        self._processed_data: list[tuple] = []

    @abstractmethod
    def validate(self, data: str) -> bool:
        ...

    @abstractmethod
    def ingest(self, data: str) -> None:
        ...

    def output(self) -> str:
        return self._processed_data


class HubProcesser(DataProcesser):
    def validate(self, data: str):
        valid: list[str] = ["start_hub", "hub", "end_hub"]
        tmp: list[str] = list(x for x in re.split(r"[: ]", data.strip()) if x)
        if len(tmp) < 5:
            return False
        if tmp[0] not in valid:
            return False
        if not all([tmp[2].lstrip("-").isdigit(), tmp[3].lstrip("-").isdigit()]):
            return False
        bracket: str = " ".join(tmp[4:])
        if not all([bracket.startswith("["), bracket.endswith("]")]):
            return False
        meta_data: list = bracket.strip("[]").split(" ")
        meta_data = [part for pair in meta_data for part in pair.split("=")]
        if len(meta_data) % 2 == 1:
            return False
        i: int = 0
        while i < len(meta_data):
            if i % 2 == 0:
                if meta_data[i] not in [
                    "color", "max_drones", "zone"
                        ]:
                    return False
            else:
                if meta_data[i - 1] == "max_drones":
                    if not meta_data[i].isdigit():
                        return False
            i += 1
        return True

    def ingest(self, data: str, line_num: int) -> None:
        if self.validate(data):
            self._processed_data.append((line_num, data))


class ConnectionProcesser(DataProcesser):
    def validate(self, data: str):
        tmp: list[str] = list(x for x in re.split(r"[ :]", data.strip()) if x)
        if len(tmp) not in (2, 3):
            return False
        if len(tmp[1].split("-")) != 2:
            return False
        if len(tmp) == 3:
            if not all([tmp[2].startswith("["), tmp[2].endswith("]")]):
                return False
            meta_data: list[str] = tmp[2].strip("[]").split("=")
            if len(meta_data) == 2:
                if meta_data[0].strip() != "max_link_capacity":
                    return False
            else:
                return False
        if tmp[0].strip() != "connection":
            return False
        return True

    def ingest(self, data: str, line_num: int) -> None:
        if self.validate(data):
            self._processed_data.append((line_num, data))


class DataStream:
    def __init__(self) -> None:
        self._processers: list[DataProcesser] = []

    def register_processer(self, prc: DataProcesser) -> None:
        self._processers.append(prc)

    def process_stream(self, stream: list[str]) -> None:
        i: int = 0
        while i < len(stream):
            for processer in self._processers:
                if processer.validate(stream[i]) is True:
                    processer.ingest(stream[i], i)
            i += 1
