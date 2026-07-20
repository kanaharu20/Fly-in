from pydantic import BaseModel, model_validator, Field
from enum import Enum
import sys
from abc import ABC, abstractmethod
from typing import Any

class ZoneTypes(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Drone(BaseModel):
    _id: int = Field(ge=0)
    _xy: tuple[int, int]

    def set_id(self, num: int) -> None:
        self._id = num

    def update_coodinate(self, xy: tuple[int, int]) -> None:
        self._xy = xy

    def reach_goal(self) -> None:
        self._at_goal = True


class Zone(BaseModel):
    _name: str
    _xy: tuple[int, int]
    _color: str
    _max_drones: int = Field(default=1, ge=1)
    _zone_type: ZoneTypes

    def set_name(self, str: str) -> None:
        self._name = str

    def set_coordinate(self, xy: tuple[int, int]) -> None:
        self._xy = xy

    def set_color(self, color: str) -> None:
        self._color = color

    def set_max_drones(self, num: int) -> None:
        self._max_drones = num

    def set_zone_type(self, type: ZoneTypes) -> None:
        self._zone_type = type

    @model_validator
    def zone_validate(self) -> "Zone":
        if any[' ' in self._name, '-' in self._name]:
            raise ValueError(
                "Zone names can use any valid "
                "characters except dashes and spaces."
            )
        return self


class Connection(BaseModel):
    _name: set
    _capacity: int = Field(default=1, ge=1)

    def set_name(self, str: str) -> None:
        self._name = str

    def set_capacity(self, num: int) -> None:
        self._capacity = num


class ProcessedData:
    def __init__(self) -> None:
        self._zone_list: list[Zone]
        self._connection_list: list[Connection]

    def append_zone(self, zone: Zone) -> None:
        self._zone_list.append(zone)

    def append_connection(self, connection: Connection) -> None:
        self._connection_list.append(connection)


class DataProcesser(ABC):
    def __init__(self) -> None:
        self._processed_data: list[str] = []

    @abstractmethod
    def validate(self, data: str) -> bool:
        ...

    @abstractmethod
    def ingest(self, data: str) -> None:
        ...


class HubProcesser(DataProcesser):
    def validate(self, data: str):
        valid: list[str] = ["start_hub", "hub", "end_hub"]
        tmp: list[str] = data.strip().split(":", " ")
        if not len(tmp) == 4:
            return False
        if tmp[0] not in valid:
            return False
        if not all[
            isinstance(tmp[2], int), isinstance(tmp[3], int)
                ]:
            return False
        if not all[
            tmp[4].startswith("["), tmp[4].endswith("]")
                ]:
            return False
        meta_data: list = tmp[4].strip("[", "]").split("=", " ")
        if meta_data % 2 == 1:
            return False
        i: int = 0
        while meta_data[i]:
            if i % 2 == 0:
                if meta_data[i] not in [
                    "color", "max_drones"
                        ]:
                    return False
            else:
                if meta_data[i - 1] == "max_drones":
                    if not isinstance(meta_data[i], int):
                        return False
            i += 1
        return True

    def ingest(self, data) -> None:
        if self.validate(data):
            self._processed_data.append(data)


class ConnectionProcesser(DataProcesser):
    def validate(self, data: str):
        tmp: list[str] = data.strip().split(":", " ")
        if len(tmp) != 2 or 3:
            return False
        if len(tmp[[1].split("-")]) != 2:
            return False
        if len(tmp) == 3:
            if not all[
                tmp[2].startswith("["), tmp[2].emdswith("]")
            ]:
                return False
            meta_data: list[str] = tmp[2].strip("[", "]").split("=")
            if meta_data == 2:
                if meta_data[0].strip() != "max_link_capacity":
                    return False
            else:
                return False
        if tmp[0].strip() != "connection":
            return False
        return True

    def ingest(self, data) -> None:
        if self.validate(data):
            self._processed_data.append(data)

