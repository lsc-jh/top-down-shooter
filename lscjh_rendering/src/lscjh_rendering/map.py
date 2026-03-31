from .lib import Layer
from .tileset import Tileset


class Map:
    def __init__(self, width: int, height: int, tileset: Tileset):
        self.__layer_count = 0
        self.__layers: list[Layer] = []
        self.__width = width
        self.__height = height
        self.__tileset = tileset

    def set_layer_count(self, count: int) -> None:
        if count < self.__layer_count:
            self.__layers = self.__layers[:count]
        else:
            for _ in range(count - self.__layer_count):
                self.__layers.append([[(0, 0) for _ in range(self.__width)] for _ in range(self.__height)])

        self.__layer_count = count

    def set_layers(self, layers: list[Layer]) -> None:
        self.__layers = layers
        self.__layer_count = len(layers)

    def add_layer(self) -> None:
        self.set_layer_count(self.__layer_count + 1)

    def tile_has_property(self, x: int, y: int, property_id: int) -> bool:
        for layer in self.__layers:
            if y >= len(layer) or x >= len(layer[y]):
                continue
            index, _ = layer[y][x]
            if self.__tileset.has_property(index, property_id):
                return True
        return False

    @property
    def layers(self) -> list[Layer]:
        return self.__layers

    def __getitem__(self, item: tuple[int, int, int]) -> tuple[int, int]:
        layer, x, y = item
        if layer >= self.__layer_count or x >= self.__width or y >= self.__height:
            raise IndexError("Layer, x, or y index out of bounds")
        return self.__layers[layer][y][x]

    def __setitem__(self, key: tuple[int, int, int], value: tuple[int, int]) -> None:
        layer, x, y = key
        if layer >= self.__layer_count or x >= self.__width or y >= self.__height:
            raise IndexError("Layer, x, or y index out of bounds")
        self.__layers[layer][y][x] = value

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height
