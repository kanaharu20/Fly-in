class process_input():
    def __init__(self):
        self._nb_drones: int
        self._start: tuple[str, int, int]
        self._goal: tuple[str, int, int]
        self._waypoints_names: list[str]
        self._waypoints: dict[str, tuple[int, int]]
        self._points_metadata: dict[tuple[int, int], list[str]]
        self._connections: str
        self._connections_meadata: dict[str, list[str] | None]

    def read_file(self) -> None:
        file_name: str = input("File name?: ")
        with open(file_name) as fd:
            raw_data: list[str] = fd.readlines(file_name)
        valid_keys: list[str] = [
            "nb_drones", "start_hub", "hub",
            "end_hub", "connection"
        ]
        tmp_dict: dict[str, str] = {}
        for line in raw_data:
            if line.strip.startswith("#"):
                continue
            tmp_list: list[str] = line.strip.split(":")
            key: str = tmp_list[0]
            value: str = tmp_list[1]
            if key not in valid_keys:
                raise ValueError(f"{key} is not expected key.")
            tmp_dict[key] = value

        for key in tmp_dict.keys:
            if key == "nb_drones":
                self._nb_drones = int(tmp_dict[key].strip)
            elif key == "connection":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) == 1:
                    self._connections = value_list[0]
                    self._connections_meadata[value_list[0]] = None
                elif len(value_list) == 2:
                    self._connections = value_list[0]
                    self._connections_meadata[value_list[0]] = value_list[1]
                else:
                    raise ValueError("connection must have 1 or 2 values.")
            elif key == "start_hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("start_hub must have 4 values")
                self._start = tuple(
                    value_list[0], int(value_list[1]), int(value_list[2])
                    )
            elif key == "end_hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("end_hub must have 4 values")
                self._goal = tuple(
                    value_list[0], int(value_list[1]), int(value_list)
                )
            elif key == "hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("end_hub must have 4 values")
                self._waypoints_names.append(value_list[0])
                coordinate: tuple[int, int] = tuple(
                    int(value_list[1]), int(value_list[2])
                    )
                self._waypoints[value_list[0]] = coordinate
                self._points_metadata[coordinate] = value_list[3]

