import pygame
import csv
from lib import load_tileset, draw_crossed_box, choose_tileset

TILE_SIZE = 8
SCALE = 4

MAP_WIDTH = 20
MAP_HEIGHT = 15

PALETTE_COLS = 5
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000


class Editor:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.level = []
        self.selected_tile = 0
        self.tiles = []
        self.blocked_tiles = set()
        self.tile_size = TILE_SIZE
        self.scale = SCALE
        self.draw_tile_size = self.tile_size * self.scale

        self.path = "assets/tileset.png"
        self.show_tile_properties = True

    def save_map(self, path):
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(self.level)
        print(f"Map saved to {path}")

    def load_map(self, path):
        with open(path, "r") as f:
            reader = csv.reader(f)
            self.level = [list(map(int, row)) for row in reader]

    def draw_palette(self):
        rows_visible = SCREEN_HEIGHT // self.draw_tile_size
        max_slots = rows_visible * PALETTE_COLS
        drawn_tiles = 0
        for i, tile in enumerate(self.tiles):
            x = (i % PALETTE_COLS) * self.draw_tile_size
            y = (i // PALETTE_COLS) * self.draw_tile_size
            self.screen.blit(tile, (x, y))
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
                tile_index = self.level[y][x]
                tile = self.tiles[tile_index]

                draw_x = PALETTE_COLS * self.draw_tile_size + x * self.draw_tile_size
                draw_y = y * self.draw_tile_size

                self.screen.blit(tile, (draw_x, draw_y))
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (draw_x, draw_y, self.draw_tile_size, self.draw_tile_size),
                    1
                )

                if tile in self.blocked_tiles and self.show_tile_properties:
                    draw_crossed_box(self.screen, x, y, self.draw_tile_size, (0, 150, 255))

    def draw_tips(self):
        palette_width = PALETTE_COLS * self.draw_tile_size

        font = pygame.font.SysFont(None, 26)

        editing_tips = "F: fill map | Right-click palette: toggle blocked | Click map: place tile"
        edit_text = font.render(editing_tips, True, (200, 200, 200))
        self.screen.blit(edit_text, (palette_width + 10, SCREEN_HEIGHT - 100))

        tips = font.render("H: toggle props | T: load tileset | S/L: save/load", True, (200, 200, 200))
        self.screen.blit(tips, (palette_width + 10, SCREEN_HEIGHT - 25))

        size_tips = f"+/-: change scale ({self.scale}x) | Shift +/-: change tile size ({self.tile_size}px)"
        size_text = font.render(size_tips, True, (200, 200, 200))
        self.screen.blit(size_text, (palette_width + 10, SCREEN_HEIGHT - 75))

        tile_info = f"Tile size: {TILE_SIZE}x{TILE_SIZE} | Map: {MAP_WIDTH}x{MAP_HEIGHT}"
        info_text = font.render(tile_info, True, (200, 200, 200))
        self.screen.blit(info_text, (palette_width + 10, SCREEN_HEIGHT - 50))

    def change_path(self, path):
        self.path = path
        self.load()

    def load(self):
        raw_tiles = load_tileset(self.path, self.tile_size)

        self.tiles = [
            pygame.transform.scale(tile, (self.draw_tile_size, self.draw_tile_size)) for tile in raw_tiles
        ]

        self.level = []
        for _ in range(MAP_HEIGHT):
            row = []
            for _ in range(MAP_WIDTH):
                row.append(0)
            self.level.append(row)

    def run(self):
        clock = pygame.time.Clock()

        running = True
        while running:
            dt = clock.tick(60)
            palette_width = PALETTE_COLS * self.draw_tile_size

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s:
                        self.save_map("map.csv")
                    if event.key == pygame.K_l:
                        self.load_map("map.csv")
                    if event.key == pygame.K_h:
                        self.show_tile_properties = not self.show_tile_properties
                    if event.key == pygame.K_t:
                        path = choose_tileset()
                        self.change_path(path)
                        self.load()
                    if event.key == pygame.K_f:
                        for y in range(MAP_HEIGHT):
                            for x in range(MAP_WIDTH):
                                self.level[y][x] = self.selected_tile

                    if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            self.tile_size = min(64, self.tile_size + 1)
                        else:
                            self.scale += 1
                        self.draw_tile_size = self.tile_size * self.scale
                        self.load()
                    if event.key == pygame.K_MINUS:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
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
                    self.level[y][x] = self.selected_tile if mouse_buttons[0] else 0

            self.screen.fill((30, 30, 30))

            self.draw_palette()
            self.draw_map()
            self.draw_tips()

            pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption("Tile Map Editor")

    editor = Editor()
    editor.load()
    editor.run()


if __name__ == "__main__":
    main()
