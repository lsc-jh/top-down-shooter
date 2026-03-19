import pygame
from pygame import Event
from lib import load_tileset, draw_crossed_box, choose_tileset
import json

TILE_SIZE = 8
SCALE = 4

MAP_WIDTH = 20
MAP_HEIGHT = 15

PALETTE_COLS = 5
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000

VIM_KEYS = [pygame.K_h, pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_DOLLAR, pygame.K_UNDERSCORE, pygame.K_g]

VIM_NAV_KEYS = {
    pygame.K_h: (-1, 0),
    pygame.K_j: (0, 1),
    pygame.K_k: (0, -1),
    pygame.K_l: (1, 0)
}

def handle_key_down(event: Event, key, callback):
    if event.key == key:
        callback()


class Editor:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.ground_level = []  # type: list[list[tuple[int, int]]]
        self.upper_level = []  # type: list[list[tuple[int, int]]]
        self.selected_level = "ground"
        self.selected_tile = 0
        self.selected_map_tile = (0, 0)
        self.current_rotation = 0
        self.tiles = []
        self.blocked_tiles = set()
        self.tile_size = TILE_SIZE
        self.scale = SCALE
        self.draw_tile_size = self.tile_size * self.scale
        self.selected_window = "palette"

        self.path = "assets/tileset.png"
        self.show_tile_properties = True

        self.running = True

    def save_map(self, path):
        data = {
            "version": 1,
            "tileset": self.path,
            "tile_size": self.tile_size,
            "scale": self.scale,
            "blocked_tiles": list(self.blocked_tiles),
            "window_size": [self.screen_width, self.screen_height],
            "layers": {
                "ground": self.ground_level,
                "upper": self.upper_level
            }
        }

        with open(path, "w") as f:
            json.dump(data, f)

        print(f"Map saved to {path}")

    def load_map(self, path):
        with open(path, "r") as f:
            data = json.load(f)

        self.path = data["tileset"]
        self.tile_size = data["tile_size"]
        self.scale = data["scale"]
        self.draw_tile_size = self.tile_size * self.scale
        self.load()

        self.blocked_tiles = set(data["blocked_tiles"])

        self.ground_level = data["layers"]["ground"]
        self.upper_level = data["layers"]["upper"]

        if "window_size" in data:
            self.screen_width, self.screen_height = data["window_size"]
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

    def draw_palette(self):
        rows_visible = self.screen_height // self.draw_tile_size
        max_slots = rows_visible * PALETTE_COLS
        drawn_tiles = 0
        for i, tile in enumerate(self.tiles):
            x = (i % PALETTE_COLS) * self.draw_tile_size
            y = (i // PALETTE_COLS) * self.draw_tile_size
            rotated_tile = pygame.transform.rotate(tile, -90 * self.current_rotation)
            self.screen.blit(rotated_tile, (x, y))
            drawn_tiles += 1

            if i in self.blocked_tiles and self.show_tile_properties:
                draw_crossed_box(self.screen, x, y, self.draw_tile_size, (0, 150, 255))

            if i == self.selected_tile:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (x, y, self.draw_tile_size, self.draw_tile_size),
                    2
                )

        for i in range(drawn_tiles, max_slots):
            x = (i % PALETTE_COLS) * self.draw_tile_size
            y = (i // PALETTE_COLS) * self.draw_tile_size
            draw_crossed_box(self.screen, x, y, self.draw_tile_size, (100, 100, 100))

    def draw_map(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                ground_index = self.ground_level[y][x][0]
                ground_tile = pygame.transform.rotate(self.tiles[ground_index], -90 * self.ground_level[y][x][1])

                upper_index = self.upper_level[y][x][0]
                upper_tile = pygame.transform.rotate(self.tiles[upper_index], -90 * self.upper_level[y][x][1])

                draw_x = PALETTE_COLS * self.draw_tile_size + x * self.draw_tile_size
                draw_y = y * self.draw_tile_size

                self.screen.blit(ground_tile, (draw_x, draw_y))
                self.screen.blit(upper_tile, (draw_x, draw_y))
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (draw_x, draw_y, self.draw_tile_size, self.draw_tile_size),
                    1
                )

                if ground_index in self.blocked_tiles or upper_index in self.blocked_tiles and self.show_tile_properties:
                    draw_crossed_box(self.screen, draw_x, draw_y, self.draw_tile_size, (0, 150, 255))
                if self.selected_window == "map" and (x, y) == self.selected_map_tile:
                    pygame.draw.rect(
                        self.screen,
                        (255, 255, 0),
                        (draw_x, draw_y, self.draw_tile_size, self.draw_tile_size),
                        2
                    )

    def draw_tips(self):
        palette_width = PALETTE_COLS * self.draw_tile_size

        font = pygame.font.SysFont(None, 26)

        map_bottom = MAP_HEIGHT * self.draw_tile_size + 10
        palette_right = palette_width + 10

        layer_text = font.render(f"Current layer: {self.selected_level.capitalize()}", True, (200, 200, 200))
        self.screen.blit(layer_text, (palette_right, map_bottom))

        rotation_text = font.render(f"Current rotation: {self.current_rotation * 90}deg", True, (200, 200, 200))
        self.screen.blit(rotation_text, (palette_right, map_bottom + 25))

        tips = "H: toggle props | T: load tileset | S/O: save/load map | F: fill layer"
        tips_text = font.render(tips, True, (200, 200, 200))
        self.screen.blit(tips_text, (palette_width + 10, self.screen_height - 25))

        scale = f"+/-: change scale ({self.scale}x)"
        scale_text = font.render(scale, True, (200, 200, 200))
        self.screen.blit(scale_text, (palette_width + 10, self.screen_height - 50))

        size = f"Shift + +/-: change tile size ({self.tile_size}px)"
        size_text = font.render(size, True, (200, 200, 200))
        self.screen.blit(size_text, (palette_width + 10, self.screen_height - 75))

    def change_path(self, path):
        self.path = path
        if self.path:
            self.load(True)

    def load(self, new_map=False):
        raw_tiles = load_tileset(self.path, self.tile_size)

        self.tiles = [
            pygame.transform.scale(tile, (self.draw_tile_size, self.draw_tile_size)) for tile in raw_tiles
        ]

        if new_map:
            self.ground_level = []
            self.upper_level = []
            for _ in range(MAP_HEIGHT):
                row = []
                for _ in range(MAP_WIDTH):
                    row.append((0, 0))  # (tile_index, rotation)
                self.ground_level.append(row[:])
                self.upper_level.append(row[:])

    def run(self):
        while self.running:
            palette_width = PALETTE_COLS * self.draw_tile_size

            for event in pygame.event.get():
                mods = pygame.key.get_mods()
                if event.type == pygame.QUIT:
                    self._quit()

                if event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size

                if event.type == pygame.KEYDOWN:
                    handle_key_down(event, pygame.K_q, self._quit)
                    handle_key_down(event, pygame.K_s, self._save)
                    handle_key_down(event, pygame.K_o, self._open)
                    handle_key_down(event, pygame.K_h, self._hide_show_properties)
                    if event.key == pygame.K_t:
                        path = choose_tileset()
                        self.change_path(path)
                    if event.key == pygame.K_f:
                        for y in range(MAP_HEIGHT):
                            for x in range(MAP_WIDTH):
                                self.ground_level[y][x] = (self.selected_tile, self.current_rotation)
                    if event.key == pygame.K_1:
                        self.selected_level = "ground"
                    if event.key == pygame.K_2:
                        self.selected_level = "upper"
                    if event.key == pygame.K_r:
                        self.current_rotation = (self.current_rotation + 1) % 4
                    if event.key in VIM_KEYS:
                        if pygame.key.get_mods() & pygame.KMOD_CTRL:
                            if event.key == pygame.K_h:
                                self.selected_window = "palette"
                                continue
                            elif event.key == pygame.K_l:
                                self.selected_window = "map"
                                continue
                        if self.selected_window == "palette":
                            if event.key in VIM_NAV_KEYS:
                                dx, dy = VIM_NAV_KEYS[event.key]
                                col = self.selected_tile % PALETTE_COLS
                                row = self.selected_tile // PALETTE_COLS
                                new_col = max(0, min(PALETTE_COLS - 1, col + dx))
                                new_row = max(0, row + dy)
                                new_index = new_row * PALETTE_COLS + new_col
                                if 0 <= new_index < len(self.tiles):
                                    self.selected_tile = new_index
                        if self.selected_window == "map":
                            if event.key in VIM_NAV_KEYS:
                                dx, dy = VIM_NAV_KEYS[event.key]
                                x, y = self.selected_map_tile
                                new_x = max(0, min(MAP_WIDTH - 1, x + dx))
                                new_y = max(0, min(MAP_HEIGHT - 1, y + dy))
                                self.selected_map_tile = (new_x, new_y)
                                if pygame.key.get_pressed()[pygame.K_SPACE]:
                                    if self.selected_level == "ground":
                                        self.ground_level[new_y][new_x] = (self.selected_tile, self.current_rotation)
                                    elif self.selected_level == "upper":
                                        self.upper_level[new_y][new_x] = (self.selected_tile, self.current_rotation)
                            if event.key == pygame.K_g:
                                if mods & pygame.KMOD_SHIFT:
                                    x, _ = self.selected_map_tile
                                    self.selected_map_tile = (x, MAP_HEIGHT - 1)
                                else:
                                    x, _ = self.selected_map_tile
                                    self.selected_map_tile = (x, 0)
                            if event.key == pygame.K_DOLLAR:
                                _, y = self.selected_map_tile
                                self.selected_map_tile = (MAP_WIDTH - 1, y)

                            if event.key == pygame.K_UNDERSCORE:
                                _, y = self.selected_map_tile
                                self.selected_map_tile = (0, y)
                    if event.key == pygame.K_SPACE:
                        x, y = self.selected_map_tile
                        if self.selected_level == "ground":
                            self.ground_level[y][x] = (self.selected_tile, self.current_rotation)
                        elif self.selected_level == "upper":
                            self.upper_level[y][x] = (self.selected_tile, self.current_rotation)

                    if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        if mods & pygame.KMOD_SHIFT:
                            self.tile_size = min(64, self.tile_size + 1)
                        else:
                            self.scale += 1
                        self.draw_tile_size = self.tile_size * self.scale
                        self.load()

                    if event.key == pygame.K_MINUS:
                        if mods & pygame.KMOD_SHIFT:
                            self.tile_size = max(4, self.tile_size - 1)
                        else:
                            self.scale = max(1, self.scale - 1)
                        self.draw_tile_size = self.tile_size * self.scale
                        self.load()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if mx < palette_width:
                        col = mx // self.draw_tile_size
                        row = my // self.draw_tile_size
                        index = row * PALETTE_COLS + col
                        if 0 <= index < len(self.tiles):
                            if event.button == 1:
                                self.selected_tile = index
                            elif event.button == 3:
                                if index in self.blocked_tiles:
                                    self.blocked_tiles.remove(index)
                                else:
                                    self.blocked_tiles.add(index)

            mx, my = pygame.mouse.get_pos()
            mouse_buttons = pygame.mouse.get_pressed()

            if mouse_buttons[0] or mouse_buttons[2]:
                x = (mx - palette_width) // self.draw_tile_size
                y = my // self.draw_tile_size
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    if self.selected_level == "ground":
                        self.ground_level[y][x] = (self.selected_tile if mouse_buttons[0] else 0, self.current_rotation)
                    elif self.selected_level == "upper":
                        self.upper_level[y][x] = (self.selected_tile if mouse_buttons[0] else 0, self.current_rotation)

            self.screen.fill((30, 30, 30))

            self.draw_palette()
            self.draw_map()
            self.draw_tips()

            pygame.display.flip()

    def _quit(self):
        self.running = False

    def _save(self):
        self.save_map("saved.json")

    def _open(self):
        self.selected_map_tile = (0, 0)
        self.current_rotation = 0
        self.selected_level = "ground"
        self.selected_tile = 0
        self.load_map("saved.json")

    def _hide_show_properties(self):
        self.show_tile_properties = not self.show_tile_properties




def main():
    pygame.init()
    pygame.display.set_caption("Tile Map Editor")

    editor = Editor()
    editor.load(True)
    editor.run()


if __name__ == "__main__":
    main()
