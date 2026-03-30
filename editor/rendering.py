from typing import Callable
import pygame
from pygame import Surface

Layer = list[list[tuple[int, int]]]

DrawCallback = Callable[[int, int, int, int], None]


class Tileset:
    def __init__(self, path: str, tile_size: int):
        self.__path = path
        self.__tile_size = tile_size
        self.tiles: list[pygame.Surface] = []
        self.__tile_properties: dict[int, set[int]] = {}

    def __load_tileset(self):
        image = pygame.image.load(self.__path).convert_alpha()
        tiles = []
        w, h = image.get_size()

        for y in range(0, h - self.__tile_size + 1, self.__tile_size):
            for x in range(0, w - self.__tile_size + 1, self.__tile_size):
                tile = image.subsurface((x, y, self.__tile_size, self.__tile_size))
                tiles.append(tile)

        empty_tile = pygame.Surface((self.__tile_size, self.__tile_size), pygame.SRCALPHA)
        tiles.insert(0, empty_tile)

        return tiles

    def load(self):
        self.tiles = self.__load_tileset()

    def get_scaled_tiles(self, scale: int) -> list[pygame.Surface]:
        return [pygame.transform.scale(tile, (self.__tile_size * scale, self.__tile_size * scale)) for tile in
                self.tiles]

    def has_property(self, tile_index: int, property_id: int) -> bool:
        return tile_index in self.__tile_properties.get(property_id, set())

    def serialize_properties(self):
        return {str(index): list(props) for index, props in self.__tile_properties.items()}

    def deserialize_properties(self, properties: dict[str, list[int]]):
        self.__tile_properties = {int(index): set(props) for index, props in properties.items()}

    def set_properties(self, properties: dict[int, set[int]]):
        self.__tile_properties = properties

    def set_property(self, tile_index: int, property_id: int):
        if tile_index not in self.__tile_properties:
            self.__tile_properties[tile_index] = set()
        self.__tile_properties[tile_index].add(property_id)

    def remove_property(self, tile_index: int, property_id: int):
        if tile_index in self.__tile_properties:
            self.__tile_properties[tile_index].discard(property_id)
            if not self.__tile_properties[tile_index]:
                del self.__tile_properties[tile_index]

    def toggle_property(self, tile_index: int, property_id: int):
        if tile_index not in self.__tile_properties:
            self.__tile_properties[tile_index] = set()
        if property_id in self.__tile_properties[tile_index]:
            self.__tile_properties[tile_index].remove(property_id)
            if not self.__tile_properties[tile_index]:
                del self.__tile_properties[tile_index]
        else:
            self.__tile_properties[tile_index].add(property_id)

    def get_properties(self, type: int) -> set[int]:
        return self.__tile_properties.get(type, set())

    def set_tile_size(self, new_size: int):
        self.__tile_size = new_size
        self.tiles = self.__load_tileset()

    def set_path(self, new_path: str):
        self.__path = new_path
        self.tiles = self.__load_tileset()

    @property
    def tile_size(self) -> int:
        return self.__tile_size

    @property
    def path(self) -> str:
        return self.__path

    @property
    def all_properties(self) -> dict[int, set[int]]:
        return self.__tile_properties


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


class Renderer:
    def __init__(self, tileset: Tileset, map_layout: Map, render_scale: int = 1):
        self.__render_scale = render_scale
        self.__tileset = tileset
        self.__tiles = self.__tileset.get_scaled_tiles(render_scale)
        self.__map = map_layout

    def set_render_scale(self, new_scale: int):
        self.__render_scale = new_scale
        self.__tiles = self.__tileset.get_scaled_tiles(new_scale)

    @property
    def tiles(self) -> list[Surface]:
        return self.__tiles

    @property
    def render_tile_size(self) -> int:
        return self.__tileset.tile_size * self.__render_scale

    def render(self, surface: Surface, offset: tuple[int, int] = (0, 0), callback: DrawCallback | None = None) -> None:
        offset_x, offset_y = offset
        for y in range(self.__map.height):
            for x in range(self.__map.width):
                draw_x = x * self.render_tile_size + offset_x
                draw_y = y * self.render_tile_size + offset_y

                for layer in self.__map.layers:
                    if y >= len(layer) or x >= len(layer[y]):
                        continue
                    index, rotation = layer[y][x]
                    if index >= len(self.__tiles):
                        continue
                    tile = pygame.transform.rotate(self.__tiles[index], -90 * rotation)
                    surface.blit(tile, (draw_x, draw_y))

                if callback:
                    try:
                        callback(x, y, draw_x, draw_y)
                    except Exception as e:
                        print(f"Error in callback for tile ({x}, {y}): {e}")
