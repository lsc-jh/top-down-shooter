from typing import Callable
import pygame
from pygame import Surface
from tileset import Tileset

Layer = list[list[tuple[int, int]]]

DrawCallback = Callable[[int, int, int, int], None]


class Map:
    def __init__(self, width: int, height: int, tile_size: int, tiles: list[Surface]):
        self.__width = width
        self.__height = height
        self.__tile_size = tile_size
        self.__tiles = tiles

    @property
    def width(self) -> int:
        return self.__width

    @property
    def height(self) -> int:
        return self.__height

    def render(self, surface: Surface, layers: list[Layer], offset: tuple[int, int] = (0, 0),
               callback: DrawCallback | None = None) -> None:
        offset_x, offset_y = offset
        for y in range(self.__height):
            for x in range(self.__width):
                draw_x = x * self.__tile_size + offset_x
                draw_y = y * self.__tile_size + offset_y

                for layer in layers:
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


class Renderer:
    def __init__(self, tileset: Tileset, render_scale: int = 1):
        self.__render_scale = render_scale
        self.__tileset = tileset
        self.__tiles = self.__tileset.get_scaled_tiles(render_scale)

    def set_render_scale(self, new_scale: int):
        self.__render_scale = new_scale
        self.__tiles = self.__tileset.get_scaled_tiles(new_scale)

    @property
    def tiles(self) -> list[Surface]:
        return self.__tiles

    @property
    def render_tile_size(self) -> int:
        return self.__tileset.tile_size * self.__render_scale

    def create_map(self, width: int, height: int) -> Map:
        return Map(width, height, self.render_tile_size, self.__tiles)
