from typing import Callable
import pygame
from pygame import Surface

Layer = list[list[tuple[int, int]]]

DrawCallback = Callable[[int, int, int, int], None]


class Renderer:
    def __init__(self, map_size: tuple[int, int], tile_size: int, tiles: list[Surface]):
        self.__width = map_size[0]
        self.__height = map_size[1]
        self.__tile_size = tile_size
        self.__tiles = tiles

    def set_map_size(self, new_size: tuple[int, int]):
        self.__width, self.__height = new_size

    def set_tile_size(self, new_size: int):
        self.__tile_size = new_size

    def set_tiles(self, new_tiles: list[Surface]):
        self.__tiles = new_tiles

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
                    tile = pygame.transform.rotate(self.__tiles[index], -90 * rotation)
                    surface.blit(tile, (draw_x, draw_y))

                if callback:
                    try:
                        callback(x, y, draw_x, draw_y)
                    except Exception as e:
                        print(f"Error in callback for tile ({x}, {y}): {e}")
