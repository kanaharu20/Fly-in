from config import ProcessedData


class MoveDrone:
    def __init__(self, data: ProcessedData):
        self._move_log: list[str] = []
        self._data: ProcessedData = data

    cost: int = 0
    