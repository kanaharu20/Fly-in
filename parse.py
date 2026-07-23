from pydantic import BaseModel, model_validator, Field, ValidationError
from enum import Enum
from abc import ABC, abstractmethod
import re
import sys


class ZoneTypes(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Drone(BaseModel):
    id: int = Field(ge=0)
    zone: Zone
    connection_to: Zone | None = None

    def set_id(self, num: int) -> None:
        self.id = num

    def get_id(self) -> int:
        return self.id

    def update_zone(self, zone: Zone) -> None:
        self.zone = zone

    def get_zone(self) -> Zone:
        return self.zone

    def set_connection_to(self, zone: Zone) -> None:
        self.connection_to = zone

    def get_connection_to(self) -> None:
        return self.connection_to


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

    def get_name(self) -> str:
        return self.name

    def get_xy(self) -> tuple[int, int]:
        return self.xy

    def get_color(self) -> str:
        return self.color

    def get_max_drones(self) -> int:
        return self.max_drones

    def reduce_max_drones(self) -> None:
        self.max_drones -= 1

    def increase_max_drones(self) -> None:
        self.max_drones += 1

    def get_zone_type(self) -> ZoneTypes:
        return self.zone_type


class Connection(BaseModel):
    name: frozenset[str]
    capacity: int = Field(default=1, ge=1)

    def get_name(self) -> frozenset[str]:
        return self.name

    def get_capa(self) -> None:
        return self.capacity

    def reduce_capa(self) -> None:
        self.capacity -= 1

    def increase_capa(self) -> None:
        self.capacity += 1


class ProcessedData:
    def __init__(self) -> None:
        self._zone_dict: dict[str, Zone] = {}
        self._connection_dict: dict[frozenset[str], Connection] = {}
        self._zone_name_list: list[str] = []
        self._start_hub: Zone
        self._end_hub: Zone
        self._drone_dict: dict[int, Drone] = {}

    def create_drones(self, nb: int) -> dict[int, Drone]:
        for id in range(nb):
            self._drone_dict[id] = Drone(
                id=id, zone=self._start_hub
                )
        return self._drone_dict

    def append_zone(self, data: list[tuple]) -> None:
        for line in data:
            tmp: list[str] = list(x for x in re.split(
                r"[: ]", line[1].strip()) if x
                    )
            keyword: str = tmp[0]
            tmp = tmp[1:]
            if tmp[0] in self._zone_name_list:
                raise ValueError(
                    f"line {line[0]}: the same name zone has been "
                    "already registered."
                    )
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
                            raise ValueError(
                                f"line {line[0]}: unknown zone type "
                                f"'{type_name}', expected "
                                f"'restricted', 'priority', or 'blocked'"
                            )
            try:
                zone: Zone = Zone(
                    name=tmp[0], xy=xy, color=color,
                    max_drones=max_drones, zone_type=zone_type
                    )
            except ValidationError as e:
                raise ValueError(f"line {line[0]}: {e}") from e
            if zone.get_xy() in list(
                xy.get_xy() for xy in self._zone_dict.values()
                    ):
                raise ValueError(
                    f"line {line[0]}: the same zone coordinate has "
                    "been already registered."
                    )
            if keyword == "start_hub":
                self._start_hub = zone
            elif keyword == "end_hub":
                self._end_hub = zone
            else:
                self._zone_dict[tmp[0]] = zone
                self._zone_name_list.append(tmp[0])

    def append_connection(self, data: list[tuple]) -> None:
        zone_name_list: list[str] = [self._start_hub.name, self._end_hub.name]
        for zone in self._zone_dict.values():
            zone_name_list.append(zone.name)
        for line in data:
            tmp: list[str] = list(x for x in re.split(
                r"[ :]", line[1].strip()) if x
                )[1:]
            zone_names = tmp[0].split("-")
            for name in zone_names:
                if name not in zone_name_list:
                    raise ValueError(
                        f"line {line[0]}: connection "
                        f"references unknown zone '{name}'; "
                        f"it must be declared as a hub first"
                    )
            name_set = frozenset(zone_names)
            max_link_capa: int = 1
            if len(tmp) > 1:
                max_link_capa = int(tmp[1].strip("[]").split("=")[1])
            if name_set in self._connection_dict:
                raise ValueError(
                    f"line {line[0]}: the same connection has "
                    "already been registered."
                    )
            try:
                connection: Connection = Connection(
                    name=name_set, capacity=max_link_capa
                )
            except ValidationError as e:
                raise ValueError(f"line {line[0]}: {e}") from e
            self._connection_dict[name_set] = connection


class DataProcesser(ABC):
    def __init__(self) -> None:
        self._processed_data: list[tuple] = []

    @abstractmethod
    def validate(self, data: str, line_num: int) -> bool:
        ...

    @abstractmethod
    def ingest(self, data: str, line_num: int) -> None:
        ...

    def output(self) -> str:
        return self._processed_data


class DroneNumProcesser(DataProcesser):
    def validate(self, data: str, line_num: int):
        tmp: list[str] = data.strip().split(":")
        if tmp[0].strip() != "nb_drones":
            return False
        if len(tmp) != 2:
            raise ValueError(
                f"line {line_num}: 'nb_drones' declaration must contain "
                f"exactly one ':', got '{data}'"
            )
        if not tmp[1].strip().isdigit():
            raise ValueError(
                f"line {line_num}: 'nb_drones' value must be a "
                f"non-negative integer, got '{tmp[1].strip()}'"
            )
        return True

    def ingest(self, data: str, line_num: int) -> None:
        tmp: list[str] = data.strip().split(":")
        self._processed_data = (line_num, int(tmp[1].strip()))


class HubProcesser(DataProcesser):
    def validate(self, data: str, line_num: int):
        valid: list[str] = ["start_hub", "hub", "end_hub"]
        tmp: list[str] = list(x for x in re.split(r"[: ]", data.strip()) if x)
        if tmp[0] not in valid:
            return False
        if len(tmp) < 5:
            raise ValueError(
                f"line {line_num}: hub declaration needs a name, x, y and "
                f"a '[...]' metadata block, got '{data}'"
            )
        if not all(
            [tmp[2].lstrip("-").isdigit(), tmp[3].lstrip("-").isdigit()]
                ):
            raise ValueError(
                f"line {line_num}: hub coordinates must be integers, "
                f"got x='{tmp[2]}' y='{tmp[3]}'"
            )
        bracket: str = " ".join(tmp[4:])
        if not all([bracket.startswith("["), bracket.endswith("]")]):
            raise ValueError(
                f"line {line_num}: hub metadata must be wrapped in "
                f"'[' and ']', got '{bracket}'"
            )
        meta_data: list = bracket.strip("[]").split(" ")
        meta_data = [part for pair in meta_data for part in pair.split("=")]
        if len(meta_data) % 2 == 1:
            raise ValueError(
                f"line {line_num}: every metadata entry needs a "
                f"'key=value' pair, got '{bracket}'"
            )
        i: int = 0
        while i < len(meta_data):
            if i % 2 == 0:
                if meta_data[i] not in [
                    "color", "max_drones", "zone"
                        ]:
                    raise ValueError(
                        f"line {line_num}: unknown metadata key "
                        f"'{meta_data[i]}', expected 'color', "
                        f"'max_drones', or 'zone'"
                    )
            else:
                if meta_data[i - 1] == "max_drones":
                    if not meta_data[i].isdigit():
                        raise ValueError(
                            f"line {line_num}: 'max_drones' must be a "
                            f"non-negative integer, got '{meta_data[i]}'"
                        )
            i += 1
        return True

    def ingest(self, data: str, line_num: int) -> None:
        if self.validate(data, line_num):
            self._processed_data.append((line_num, data))


class ConnectionProcesser(DataProcesser):
    def validate(self, data: str, line_num: int):
        tmp: list[str] = list(x for x in re.split(r"[ :]", data.strip()) if x)
        if tmp[0].strip() != "connection":
            return False
        if len(tmp) not in (2, 3):
            raise ValueError(
                f"line {line_num}: connection declaration must have 1 or 2 "
                f"fields after 'connection:', got '{data}'"
            )
        if len(tmp[1].split("-")) != 2:
            raise ValueError(
                f"line {line_num}: connection must link exactly two zone "
                f"names joined by '-', got '{tmp[1]}'"
            )
        if len(tmp) == 3:
            if not all([tmp[2].startswith("["), tmp[2].endswith("]")]):
                raise ValueError(
                    f"line {line_num}: connection metadata must be "
                    f"wrapped in '[' and ']', got '{tmp[2]}'"
                )
            meta_data: list[str] = tmp[2].strip("[]").split("=")
            if len(meta_data) == 2:
                if meta_data[0].strip() != "max_link_capacity":
                    raise ValueError(
                        f"line {line_num}: only 'max_link_capacity' is "
                        f"allowed in connection metadata, got "
                        f"'{meta_data[0].strip()}'"
                    )
            else:
                raise ValueError(
                    f"line {line_num}: connection metadata must be a "
                    f"single 'key=value' pair, got '{tmp[2]}'"
                )
        return True

    def ingest(self, data: str, line_num: int) -> None:
        if self.validate(data, line_num):
            self._processed_data.append((line_num, data))


class DataStream:
    def __init__(self) -> None:
        self._processers: list[DataProcesser] = []

    def register_processer(self, prc: DataProcesser) -> None:
        self._processers.append(prc)

    def process_stream(self, stream: list[str]) -> None:
        i: int = 0
        while i < len(stream):
            if not stream[i] or stream[i].startswith("#"):
                i += 1
                continue
            is_processed: int = 0
            for processer in self._processers:
                if processer.validate(stream[i], i) is True:
                    processer.ingest(stream[i], i)
                    is_processed = 1
                    break
            if is_processed == 0:
                raise ValueError(
                    f"line {i}: unrecognized declaration, expected "
                    f"'nb_drones', 'hub'/'start_hub'/'end_hub', or "
                    f"'connection', got '{stream[i]}'"
                )
            i += 1


def read_file() -> list[str]:
    argv: list[str] = sys.argv
    filename: str = argv[1]
    with open(filename) as fd:
        raw: list[str] = fd.readlines()
    ret: list[str] = []
    for line in raw:
        ret.append(line.strip())
    meaningful: list[str] = [
        line for line in ret if line and not line.startswith("#")
        ]
    if not meaningful or not meaningful[0].startswith("nb_drones"):
        raise ValueError(
            "'nb_drones' must be the first declaration in the file "
            "(blank lines and '#' comments are skipped)."
            )
    for line in meaningful[1:]:
        if line.startswith("nb_drones"):
            raise ValueError(
                "'nb_drones' must be declared exactly once, at the top "
                "of the file."
                )

    return ret


def setup() -> None:
    config: list[str] = read_file()
    hubprc = HubProcesser()
    conprc = ConnectionProcesser()
    dronenumprc = DroneNumProcesser()
    datastream = DataStream()
    prcddata = ProcessedData()
    datastream.register_processer(hubprc)
    datastream.register_processer(conprc)
    datastream.register_processer(dronenumprc)
    datastream.process_stream(config)
    prcddata.append_zone(hubprc.output())
    prcddata.append_connection(conprc.output())
    prcddata.create_drones(dronenumprc.output()[1])
