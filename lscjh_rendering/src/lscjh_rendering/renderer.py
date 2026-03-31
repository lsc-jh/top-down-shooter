from .lib import DrawCallback
from .tileset import Tileset
from .map import Map
import pygame
from pygame import Surface


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
