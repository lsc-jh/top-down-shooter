import os.path
import warnings
from lib import draw_crossed_box, choose_tileset, handle_key_down, get_number_key_index, get_absolute_path, \
    get_home_directory
import json
from constants import *
from tileforge import Map, Tileset, Renderer

SAVE_FILE_NAME = "tileset-editor-save.json"
EXPORT_FILE_NAME = "tileset-editor-export"

IGNORE_MESSAGE = "Requested window was forcibly resized by the OS."


class Editor:
    def __init__(self):
        self.screen_width = SCREEN_WIDTH
        self.screen_height = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)
        self.selected_level = 0
        self.selected_tile = 0
        self.selected_map_tile: tuple[int, int] = (0, 0)
        self.selected_marker = 1
        self.current_rotation = 0
        self.tile_size = TILE_SIZE
        self.scale = SCALE
        self.selected_window = "palette"

        self.path = get_absolute_path("assets/tileset.png")
        self.show_tile_properties = True
        self.show_borders = True

        self.running = True
        self.tileset = Tileset(self.path, self.tile_size)
        self.tileset.load()
        self.map = Map(MAP_WIDTH, MAP_HEIGHT)
        self.map.set_layer_count(4)
        self.renderer = Renderer(self.tileset, self.map, self.scale)

    def save_map(self, path):
        data = {
            "version": 1,
            "tileset": self.path,
            "tile_size": self.tile_size,
            "scale": self.scale,
            "tile_properties": self.tileset.serialize_properties(),
            "window_size": [self.screen_width, self.screen_height],
            "layers": self.map.layers,
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
        self.map.set_layers(data["layers"])
        self.tileset.deserialize_properties(data.get("tile_properties", {}))

        if "window_size" in data:
            self.screen_width, self.screen_height = data["window_size"]
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.RESIZABLE)

        self.tileset.set_path(self.path)
        self.tileset.set_tile_size(self.tile_size)
        self.renderer.set_render_scale(self.scale)

    def export_map(self, path):
        export_data = {
            "tileset": self.path,
            "tile_size": self.tile_size,
            "blocked_tiles": list(self.tileset.get_properties(1)),
            "pathfinding_tiles": list(self.tileset.get_properties(2)),
            "layers": self.map.layers,
            "bottom_grid": [[self.map[0, x, y][0] for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)],
        }

        with open(path, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"Map exported to {path}")

    def export_map_as_image(self, path):
        map_width_px = MAP_WIDTH * self.renderer.render_tile_size
        map_height_px = MAP_HEIGHT * self.renderer.render_tile_size
        image = pygame.Surface((map_width_px, map_height_px), pygame.SRCALPHA)
        self.renderer.render(image)
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

            if self.show_tile_properties:
                if self.tileset.has_property(i, 1):
                    draw_crossed_box(self.screen, x, y, self.renderer.render_tile_size, (0, 150, 255))
                if self.tileset.has_property(i, 2):
                    draw_crossed_box(self.screen, x, y, self.renderer.render_tile_size, (255, 0, 150))

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

    def draw_map(self):
        def callback(x, y, draw_x, draw_y):
            if self.show_borders:
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (draw_x, draw_y, self.renderer.render_tile_size, self.renderer.render_tile_size),
                    1
                )

            if self.show_tile_properties and self.map.cell_has_property(self.tileset, (x, y), 1):
                draw_crossed_box(self.screen, draw_x, draw_y, self.renderer.render_tile_size, (0, 150, 255))
            if self.show_tile_properties and self.map.cell_has_property(self.tileset, (x, y), 2):
                draw_crossed_box(self.screen, draw_x, draw_y, self.renderer.render_tile_size, (255, 0, 150))

            if self.selected_window == "map" and (x, y) == self.selected_map_tile:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (draw_x, draw_y, self.renderer.render_tile_size, self.renderer.render_tile_size),
                    2
                )

        offset = (PALETTE_COLS * self.renderer.render_tile_size + 10, 0)
        self.renderer.render(self.screen, offset, callback=callback)

    def draw_tile_preview(self, tile_index):
        left_of_map = PALETTE_COLS * self.renderer.render_tile_size + MAP_WIDTH * self.renderer.render_tile_size + 20
        if left_of_map + self.renderer.render_tile_size * self.scale > self.screen_width:
            return
        x = left_of_map
        y = 10
        tile = self.renderer.tiles[tile_index]
        scaled_size = self.renderer.render_tile_size * self.scale
        scaled_tile = pygame.transform.scale(tile, (scaled_size, scaled_size))
        rotated_tile = pygame.transform.rotate(scaled_tile, -90 * self.current_rotation)
        self.screen.blit(rotated_tile, (x, y))
        font = pygame.font.SysFont(None, 24)
        props = []
        if self.tileset.has_property(tile_index, 1):
            props.append("Blocked")
        if self.tileset.has_property(tile_index, 2):
            props.append("Pathfinding")
        text = font.render(", ".join(props), True, (255, 255, 255))
        self.screen.blit(text, (x, y + scaled_size + 5))

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
                    handle_key_down(event, ARROW_KEYS, self._handle_vim_navigation)

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
                                self.tileset.toggle_property(index, self.selected_marker)

            mx, my = pygame.mouse.get_pos()
            mouse_buttons = pygame.mouse.get_pressed()

            if mouse_buttons[0] or mouse_buttons[2]:
                x = (mx - palette_width) // self.renderer.render_tile_size
                y = my // self.renderer.render_tile_size
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    self.map[self.selected_level, x, y] = (self.selected_tile if mouse_buttons[0] else 0,
                                                           self.current_rotation)

            self.screen.fill((30, 30, 30))

            self.draw_palette()
            self.draw_map()
            self.draw_tile_preview(self.selected_tile)
            self.draw_tips()

            pygame.display.flip()

    def _quit(self, _e):
        self.running = False

    def _save(self, _e):
        path = os.path.join(get_home_directory(), SAVE_FILE_NAME)
        self.save_map(path)

    def _open(self, _e):
        self.selected_map_tile = (0, 0)
        self.current_rotation = 0
        self.selected_level = 0
        self.selected_tile = 0
        path = os.path.join(get_home_directory(), SAVE_FILE_NAME)
        self.load_map(path)

    def _export(self, _e):
        path = os.path.join(get_home_directory(), EXPORT_FILE_NAME)
        self.export_map(f"{path}.json")
        self.export_map_as_image(f"{path}.png")

    def _select_tileset(self, _e):
        path = choose_tileset()
        self.change_path(path)

    def _fill_layer(self, _e):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                self.map[self.selected_level, x, y] = (self.selected_tile, self.current_rotation)

    def _handle_rotation(self, _e):
        self.current_rotation = (self.current_rotation + 1) % 4

    def _place_tile(self, _e):
        x, y = self.selected_map_tile
        self.map[self.selected_level, x, y] = (self.selected_tile, self.current_rotation)

    def _handle_tile_size_increase(self, _e):
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            self.tile_size = min(64, self.tile_size + 1)
        else:
            self.scale += 1
        self.tileset.set_tile_size(self.tile_size)

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

        if number in [1, 2] and is_shift:
            self.selected_marker = number

        return False

    def _handle_vim_navigation(self, event):
        mods = pygame.key.get_mods()
        if self.selected_window == "palette":
            if event.key in VIM_NAV_KEYS or event.key in ARROW_NAV_KEYS:
                dx, dy = VIM_NAV_KEYS[event.key] if event.key in VIM_NAV_KEYS else ARROW_NAV_KEYS[event.key]
                col = self.selected_tile % PALETTE_COLS
                row = self.selected_tile // PALETTE_COLS
                new_col = max(0, min(PALETTE_COLS - 1, col + dx))
                new_row = max(0, row + dy)
                new_index = new_row * PALETTE_COLS + new_col
                if 0 <= new_index < len(self.renderer.tiles):
                    self.selected_tile = new_index
        if self.selected_window == "map":
            if event.key in VIM_NAV_KEYS or event.key in ARROW_NAV_KEYS:
                dx, dy = VIM_NAV_KEYS[event.key] if event.key in VIM_NAV_KEYS else ARROW_NAV_KEYS[event.key]
                x, y = self.selected_map_tile
                new_x = max(0, min(MAP_WIDTH - 1, x + dx))
                new_y = max(0, min(MAP_HEIGHT - 1, y + dy))
                self.selected_map_tile = (new_x, new_y)
                if pygame.key.get_pressed()[pygame.K_SPACE]:
                    self.map[self.selected_level, new_x, new_y] = (self.selected_tile, self.current_rotation)
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
    editor.run()


if __name__ == "__main__":
    try:
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=RuntimeWarning, message=IGNORE_MESSAGE)
            main()

    except KeyboardInterrupt:
        print("Bye! Enjoy your day :)")
