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

    def append_connection(self, connection:Connection) -> None:
        self._connection_list.append(connection)


class DataProcesser(ABC):
    def __init__(self) -> None:
        self._processed_data: list[Any] = []

    @abstractmethod
    def validate(self, data: str) -> bool:
        ...

    @abstractmethod
    def ingest(self, data: str) -> None:
        ...


class HubProcesser(DataProcesser):
    def validate(self, data: str):
        tmp: list[str] = data.strip().split(":")
        if "connection" in tmp[0]:
            if len(tmp) == 2:
                if len(tmp[1].sprit("-")) == 2:
                    return True
                elif len(tmp) == 3:
                    if "max_link_capacity=" in tmp[2]:
                        if tmp[2].startswith(
                            "["
                            ) and tmp[2].endswith("]"):
                            return True
        else:
            return False

    def ingest(self, data):
        if self.validate(data):
            self._processed_data.append()
        return super().ingest(data)


class ConnectionProcesser(DataProcesser):
