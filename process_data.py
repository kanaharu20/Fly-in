class process_input():
    def __init__(self):
        self._nb_drones: int
        self._start: tuple[str, int, int]
        self._goal: tuple[str, int, int]
        self._waypoints_names: list[str]
        self._waypoints: dict[str, tuple]
        self._points_metadata: dict[tuple[int, int], list[str]]
        self._connections: tuple[str, str]
        self._connections_meadata: dict[tuple, list[str]]

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
                if len(value_list) != 2:
                    raise ValueError("connection must have 2 values.")
                
            elif key == "start_hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("start_hub must have 4 values")

            elif key == "end_hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("end_hub must have 4 values")
            elif key == "hub":
                value_list: list[str] = tmp_dict[key].strip.split(" ")
                if len(value_list) != 4:
                    raise ValueError("end_hub must have 4 values")
