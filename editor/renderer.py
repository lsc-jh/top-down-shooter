from typing import Callable
import pygame
from pygame import Surface

Layer = list[list[tuple[int, int]]]

DrawCallback = Callable[[int, int, int, int], None]


def load_tileset(path, tile_size):
    image = pygame.image.load(path).convert_alpha()
    tiles = []
    w, h = image.get_size()

    for y in range(0, h - tile_size + 1, tile_size):
        for x in range(0, w - tile_size + 1, tile_size):
            tile = image.subsurface((x, y, tile_size, tile_size))
            tiles.append(tile)

    empty_tile = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
    tiles.insert(0, empty_tile)

    return tiles


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
                    tile = pygame.transform.rotate(self.__tiles[index], -90 * rotation)
                    surface.blit(tile, (draw_x, draw_y))

                if callback:
                    try:
                        callback(x, y, draw_x, draw_y)
                    except Exception as e:
                        print(f"Error in callback for tile ({x}, {y}): {e}")


class Renderer:
    def __init__(self, path: str, tile_size: int, render_scale: int = 1):
        self.__path = path
        self.__tile_size = tile_size
        self.__render_scale = render_scale
        self.__raw_tiles = load_tileset(path, tile_size)
        rendered_size = tile_size * render_scale
        self.__tiles = [pygame.transform.scale(tile, (rendered_size, rendered_size)) for tile in self.__raw_tiles]

    def set_tile_size(self, new_size: int):
        self.__tile_size = new_size
        self.__raw_tiles = load_tileset(self.__path, new_size)
        self.__tiles = [pygame.transform.scale(tile, (self.render_tile_size, self.render_tile_size)) for tile in
                        self.__raw_tiles]

    def set_render_scale(self, new_scale: int):
        self.__render_scale = new_scale
        self.__tiles = [pygame.transform.scale(tile, (self.render_tile_size, self.render_tile_size)) for tile in
                        self.__raw_tiles]

    def set_path(self, new_path: str):
        self.__path = new_path
        self.__raw_tiles = load_tileset(new_path, self.__tile_size)
        self.__tiles = [pygame.transform.scale(tile, (self.render_tile_size, self.render_tile_size)) for tile in
                        self.__raw_tiles]

    @property
    def tiles(self) -> list[Surface]:
        return self.__tiles

    @property
    def render_tile_size(self) -> int:
        return self.__tile_size * self.__render_scale

    def create_map(self, width: int, height: int) -> Map:
        return Map(width, height, self.render_tile_size, self.__tiles)
