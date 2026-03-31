import pygame


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
