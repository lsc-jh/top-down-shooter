from typing import Callable

Layer = list[list[tuple[int, int]]]
DrawCallback = Callable[[int, int, int, int], None]
