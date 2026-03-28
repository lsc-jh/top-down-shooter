import pygame
from pygame import Event
from lib import draw_crossed_box, choose_tileset
import json
from typing import Callable
from renderer import Renderer, Layer

TILE_SIZE = 8
SCALE = 4

MAP_WIDTH = 20
MAP_HEIGHT = 15

PALETTE_COLS = 5
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000

VIM_KEYS = [pygame.K_h, pygame.K_j, pygame.K_k, pygame.K_l]

NUMBERS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]

VIM_NAV_KEYS = {
    pygame.K_h: (-1, 0),
    pygame.K_j: (0, 1),
    pygame.K_k: (0, -1),
    pygame.K_l: (1, 0)
}


def get_number_key_index(event: Event):
    if event.key in NUMBERS:
        return NUMBERS.index(event.key) + 1
    return 0


def handle_key_down(event: Event, keys: int | list[int], callback: Callable[[Event], bool | None]):
    if isinstance(keys, int):
        if event.key == keys:
            return callback(event)
        return None

    if event.key in keys:
        return callback(event)

    return None


class Editor:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.layer_count = 4
        self.layers: list[Layer] = [[] for _ in range(self.layer_count)]
        self.selected_level = 0
        self.selected_tile = 0
        self.selected_map_tile = (0, 0)
        self.current_rotation = 0
        self.blocked_tiles = set()
        self.tile_size = TILE_SIZE
        self.scale = SCALE
        self.selected_window = "palette"

        self.path = "assets/tileset.png"
        self.show_tile_properties = True
        self.show_borders = True

        self.running = True
        self.renderer = Renderer(self.path, self.tile_size, self.scale)

    def save_map(self, path):
        data = {
            "version": 1,
            "tileset": self.path,
            "tile_size": self.tile_size,
            "scale": self.scale,
            "blocked_tiles": list(self.blocked_tiles),
            "window_size": [self.screen_width, self.screen_height],
            "layers": self.layers,
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
        self.reset_layers()

        self.blocked_tiles = set(data["blocked_tiles"])
        self.layers = data["layers"]
        if len(self.layers) < self.layer_count:
            for _ in range(self.layer_count - len(self.layers)):
                self.layers.append([[(0, 0) for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)])

        if "window_size" in data:
            self.screen_width, self.screen_height = data["window_size"]
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        self.renderer.set_tile_size(self.tile_size)
        self.renderer.set_render_scale(self.scale)
        self.renderer.set_path(self.path)

    def export_map(self, path):
        export_data = {
            "tileset": self.path,
            "tile_size": self.tile_size,
            "blocked_tiles": list(self.blocked_tiles),
            "layers": self.layers,
        }

        with open(path, "w") as f:
            json.dump(export_data, f)

        print(f"Map exported to {path}")

    def export_map_as_image(self, path):
        map_width_px = MAP_WIDTH * self.renderer.render_tile_size
        map_height_px = MAP_HEIGHT * self.renderer.render_tile_size
        image = pygame.Surface((map_width_px, map_height_px), pygame.SRCALPHA)
        _map = self.renderer.create_map(MAP_WIDTH, MAP_HEIGHT)
        _map.render(image, self.layers)
        pygame.image.save(image, path)
        print(f"Map exported as image to {path}")

    def draw_palette(self):
        rows_visible = self.screen_height // self.renderer.render_tile_size
        max_slots = rows_visible * PALETTE_COLS
        drawn_tiles = 0
        for i, tile in enumerate(self.renderer.tiles):
            x = (i % PALETTE_COLS) * self.renderer.render_tile_size
            y = (i // PALETTE_COLS) * self.renderer.render_tile_size
            rotated_tile = pygame.transform.rotate(tile, -90 * self.current_rotation)
            self.screen.blit(rotated_tile, (x, y))
            drawn_tiles += 1

            if i in self.blocked_tiles and self.show_tile_properties:
                draw_crossed_box(self.screen, x, y, self.renderer.render_tile_size, (0, 150, 255))

            if i == self.selected_tile:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (x, y, self.renderer.render_tile_size, self.renderer.render_tile_size),
                    2
                )

        for i in range(drawn_tiles, max_slots):
            x = (i % PALETTE_COLS) * self.renderer.render_tile_size
            y = (i // PALETTE_COLS) * self.renderer.render_tile_size
            draw_crossed_box(self.screen, x, y, self.renderer.render_tile_size, (100, 100, 100))

    def is_blocked(self, x, y):
        if not self.show_tile_properties:
            return False

        for layer in self.layers:
            index = layer[y][x][0]
            if index in self.blocked_tiles:
                return True

        return False

    def draw_map(self):
        def callback(x, y, draw_x, draw_y):
            if self.show_borders:
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (draw_x, draw_y, self.renderer.render_tile_size, self.renderer.render_tile_size),
                    1
                )

            if self.show_tile_properties and self.is_blocked(x, y):
                draw_crossed_box(self.screen, draw_x, draw_y, self.renderer.render_tile_size, (0, 150, 255))

            if self.selected_window == "map" and (x, y) == self.selected_map_tile:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (draw_x, draw_y, self.renderer.render_tile_size, self.renderer.render_tile_size),
                    2
                )

        _map = self.renderer.create_map(MAP_WIDTH, MAP_HEIGHT)
        _map.render(self.screen, self.layers, (PALETTE_COLS * self.renderer.render_tile_size, 0), callback=callback)

    def draw_tips(self):
        palette_width = PALETTE_COLS * self.renderer.render_tile_size
        font = pygame.font.SysFont(None, 24)

        map_bottom = MAP_HEIGHT * self.renderer.render_tile_size + 10
        palette_right = palette_width + 10

        tips = [
            "Q: Quit",
            "S: Save",
            "O: Open",
            "E: Export",
            "Shift + 1-4: Toggle Layer Visibility (not implemented)",
            "Ctrl + 1: Toggle Tile Properties",
            "Ctrl + 2: Toggle Borders"
            "T: Select Tileset",
            "F: Fill Layer",
            "R: Rotate Tile",
            "Space: Place Tile",
            "+/-: Change Tile Scale (ctrl for changing the tile size)",
            "Ctrl + H/L: Switch between Palette and Map",
            "Vim Keys (HJKL) to navigate in selected panel",
            "G to go to start/end of column (with Shift for end/start)",
        ]

        available_tips = (self.screen_height - map_bottom) // 30

        for i, tip in enumerate(tips):
            if i >= available_tips:
                text = font.render(tip, True, (255, 255, 0))
                text_size = text.get_size()
                left = self.screen_width - text_size[0] - 10
                top = map_bottom + (i - available_tips) * 30
                self.screen.blit(text, (left, top))
            else:
                text = font.render(tip, True, (200, 200, 200))
                self.screen.blit(text, (palette_right, map_bottom + i * 30))

    def change_path(self, path):
        self.path = path
        self.reset_layers()

    def reset_layers(self):
        self.layers = [[] for _ in range(self.layer_count)]
        for _ in range(MAP_HEIGHT):
            row = []
            for _ in range(MAP_WIDTH):
                row.append((0, 0))  # (tile_index, rotation)

            for layer in self.layers:
                layer.append(row[:])

    def run(self):
        while self.running:
            palette_width = PALETTE_COLS * self.renderer.render_tile_size
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                if event.type == pygame.VIDEORESIZE:
                    self.screen_width, self.screen_height = event.size

                if event.type == pygame.KEYDOWN:
                    # Shift + Number to toggle properties, normal numbers to change laters
                    if handle_key_down(event, NUMBERS, self._handle_properties_toggle):
                        continue
                    # the panel change has to stop the chain because it's just normal vim
                    # navigation with the ctrl held down
                    if handle_key_down(event, VIM_KEYS, self._handle_selected_panel_change):
                        continue
                    handle_key_down(event, pygame.K_q, self._quit)
                    handle_key_down(event, pygame.K_s, self._save)
                    handle_key_down(event, pygame.K_o, self._open)
                    handle_key_down(event, pygame.K_e, self._export)
                    handle_key_down(event, pygame.K_t, self._select_tileset)
                    handle_key_down(event, pygame.K_f, self._fill_layer)
                    handle_key_down(event, NUMBERS, self._handle_change_layer)
                    handle_key_down(event, pygame.K_r, self._handle_rotation)
                    handle_key_down(event, pygame.K_SPACE, self._place_tile)
                    handle_key_down(event, pygame.K_EQUALS, self._handle_tile_size_increase)
                    handle_key_down(event, pygame.K_MINUS, self._handle_tile_size_decrease)
                    handle_key_down(event, VIM_KEYS, self._handle_vim_navigation)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if mx < palette_width:
                        col = mx // self.renderer.render_tile_size
                        row = my // self.renderer.render_tile_size
                        index = row * PALETTE_COLS + col
                        if 0 <= index < len(self.renderer.tiles):
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
                x = (mx - palette_width) // self.renderer.render_tile_size
                y = my // self.renderer.render_tile_size
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    self.layers[self.selected_level][y][x] = (self.selected_tile if mouse_buttons[0] else 0,
                                                              self.current_rotation)

            self.screen.fill((30, 30, 30))

            self.draw_palette()
            self.draw_map()
            self.draw_tips()

            pygame.display.flip()

    def _quit(self, _e):
        self.running = False

    def _save(self, _e):
        self.save_map("saved.json")

    def _open(self, _e):
        self.selected_map_tile = (0, 0)
        self.current_rotation = 0
        self.selected_level = 0
        self.selected_tile = 0
        self.load_map("saved.json")

    def _export(self, _e):
        self.export_map("exported.json")
        self.export_map_as_image("exported.png")

    def _select_tileset(self, _e):
        path = choose_tileset()
        self.change_path(path)

    def _fill_layer(self, _e):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                self.layers[self.selected_level][y][x] = (self.selected_tile, self.current_rotation)

    def _handle_rotation(self, _e):
        self.current_rotation = (self.current_rotation + 1) % 4

    def _place_tile(self, _e):
        x, y = self.selected_map_tile
        self.layers[self.selected_level][y][x] = (self.selected_tile, self.current_rotation)

    def _handle_tile_size_increase(self, _e):
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            self.tile_size = min(64, self.tile_size + 1)
        else:
            self.scale += 1
        self.renderer.set_tile_size(self.tile_size)

    def _handle_tile_size_decrease(self, _e):
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_SHIFT:
            self.tile_size = max(4, self.tile_size - 1)
        else:
            self.scale = max(1, self.scale - 1)
        self.renderer.set_render_scale(self.scale)

    def _handle_selected_panel_change(self, event):
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            if event.key == pygame.K_h:
                self.selected_window = "palette"
                return True
            elif event.key == pygame.K_l:
                self.selected_window = "map"
                return True

        return False

    def _handle_change_layer(self, event):
        self.selected_level = get_number_key_index(event)

    def _handle_properties_toggle(self, event):
        mods = pygame.key.get_mods()
        if mods == 0:
            return False
        is_ctrl = mods & pygame.KMOD_CTRL
        is_shift = mods & pygame.KMOD_SHIFT
        is_command = mods & pygame.KMOD_META

        number = get_number_key_index(event)
        if number == 1 and (is_ctrl or is_command):
            self.show_tile_properties = not self.show_tile_properties
            return True

        if number == 2 and (is_ctrl or is_command):
            self.show_borders = not self.show_borders
            return True

        return False

    def _handle_vim_navigation(self, event):
        mods = pygame.key.get_mods()
        if self.selected_window == "palette":
            if event.key in VIM_NAV_KEYS:
                dx, dy = VIM_NAV_KEYS[event.key]
                col = self.selected_tile % PALETTE_COLS
                row = self.selected_tile // PALETTE_COLS
                new_col = max(0, min(PALETTE_COLS - 1, col + dx))
                new_row = max(0, row + dy)
                new_index = new_row * PALETTE_COLS + new_col
                if 0 <= new_index < len(self.renderer.tiles):
                    self.selected_tile = new_index
        if self.selected_window == "map":
            if event.key in VIM_NAV_KEYS:
                dx, dy = VIM_NAV_KEYS[event.key]
                x, y = self.selected_map_tile
                new_x = max(0, min(MAP_WIDTH - 1, x + dx))
                new_y = max(0, min(MAP_HEIGHT - 1, y + dy))
                self.selected_map_tile = (new_x, new_y)
                if pygame.key.get_pressed()[pygame.K_SPACE]:
                    self.layers[self.selected_level][new_y][new_x] = (self.selected_tile, self.current_rotation)
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


def main():
    pygame.init()
    pygame.display.set_caption("Tile Map Editor")

    editor = Editor()
    editor.reset_layers()
    editor.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bye! Enjoy your day :)")
