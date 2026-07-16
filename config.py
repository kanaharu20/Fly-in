from pydantic import BaseModel, model_validator, Field
from enum import Enum


class ZoneTypes(Enum):
    NORMAL = "normal"
    RESTRICTED = "restricted"
    PRIORITY = "priority"
    BLOCKED = "blocked"


class Drone(BaseModel):
    _id: int = Field(ge=0)
    _xy: tuple[int, int]
    _at_goal: bool = Field(default=False)

    def set_id(self, num: int) -> None:
        self._id = num

    def update_coodinate(self, xy: tuple[int, int]) -> None:
        self._xy = xy

    def reach_goal(self) -> None:
        self._at_goal = True

    @classmethod
    def create_drone_cls(cls) -> Drone:
        return cls()


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

    @model_validator
    def zone_validate(self) -> "Zone":
        if any[' ' in self._name, '-' in self._name]:
            raise ValueError(
                "Zone names can use any valid "
                "characters except dashes and spaces."
            )
        return self

    @classmethod
    def create_zone_cls(cls) -> Zone:
        return cls()


class Connection(BaseModel):
    _name: str
    _capacity: int = Field(default=1, ge=1)

    def set_name(self, str: str) -> None:
        self._name = str

    def set_capacity(self, num: int) -> None:
        self._capacity = num
