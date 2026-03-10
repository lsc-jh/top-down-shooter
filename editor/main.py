import pygame
import csv

TILE_SIZE = 16
SCALE = 3
DRAW_TILE_SIZE = TILE_SIZE * SCALE

MAP_WIDTH = 20
MAP_HEIGHT = 15

PALETTE_COLS = 5
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900


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


def draw_crossed_box(screen, x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size, size), 1)
    pygame.draw.line(screen, color, (x, y), (x + size, y + size), 1)
    pygame.draw.line(screen, color, (x + size, y), (x, y + size), 1)


class Editor:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.level = []
        self.selected_tile = 0
        self.tiles = []
        self.blocked_tiles = set()

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
        rows_visible = SCREEN_HEIGHT // DRAW_TILE_SIZE
        max_slots = rows_visible * PALETTE_COLS
        drawn_tiles = 0
        for i, tile in enumerate(self.tiles):
            x = (i % PALETTE_COLS) * DRAW_TILE_SIZE
            y = (i // PALETTE_COLS) * DRAW_TILE_SIZE
            self.screen.blit(tile, (x, y))
            drawn_tiles += 1

            if i in self.blocked_tiles and self.show_tile_properties:
                draw_crossed_box(self.screen, x, y, DRAW_TILE_SIZE, (0, 150, 255))

            if i == self.selected_tile:
                pygame.draw.rect(
                    self.screen,
                    (255, 255, 0),
                    (x, y, DRAW_TILE_SIZE, DRAW_TILE_SIZE),
                    2
                )

        for i in range(drawn_tiles, max_slots):
            x = (i % PALETTE_COLS) * DRAW_TILE_SIZE
            y = (i // PALETTE_COLS) * DRAW_TILE_SIZE
            draw_crossed_box(self.screen, x, y, DRAW_TILE_SIZE, (100, 100, 100))

    def draw_map(self):
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                tile_index = self.level[y][x]
                tile = self.tiles[tile_index]

                draw_x = PALETTE_COLS * DRAW_TILE_SIZE + x * DRAW_TILE_SIZE
                draw_y = y * DRAW_TILE_SIZE

                self.screen.blit(tile, (draw_x, draw_y))
                pygame.draw.rect(
                    self.screen,
                    (60, 60, 60),
                    (draw_x, draw_y, DRAW_TILE_SIZE, DRAW_TILE_SIZE),
                    1
                )

                if tile in self.blocked_tiles and self.show_tile_properties:
                    draw_crossed_box(self.screen, x, y, DRAW_TILE_SIZE, (0, 150, 255))

    def load(self, path):
        raw_tiles = load_tileset(path, TILE_SIZE)

        self.tiles = [
            pygame.transform.scale(tile, (DRAW_TILE_SIZE, DRAW_TILE_SIZE)) for tile in raw_tiles
        ]

        self.level = []
        for _ in range(MAP_HEIGHT):
            row = []
            for _ in range(MAP_WIDTH):
                row.append(0)
            self.level.append(row)

    def run(self):
        clock = pygame.time.Clock()

        palette_width = PALETTE_COLS * DRAW_TILE_SIZE

        running = True
        while running:
            dt = clock.tick(60)

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

                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if mx < palette_width:
                        col = mx // DRAW_TILE_SIZE
                        row = my // DRAW_TILE_SIZE
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
                x = (mx - palette_width) // DRAW_TILE_SIZE
                y = my // DRAW_TILE_SIZE
                if 0 <= x < MAP_WIDTH and 0 <= y < MAP_HEIGHT:
                    self.level[y][x] = self.selected_tile if mouse_buttons[0] else 0

            self.screen.fill((30, 30, 30))

            self.draw_palette()
            self.draw_map()

            font = pygame.font.SysFont(None, 36)
            label = font.render("H: toggle props | T: load tileset | S/L: save/load", True, (200, 200, 200))
            self.screen.blit(label, (palette_width + 10, SCREEN_HEIGHT - 25))

            pygame.display.flip()


def main():
    pygame.init()
    pygame.display.set_caption("Tile Map Editor")

    editor = Editor()
    editor.load("assets/TILES.png")
    editor.run()


if __name__ == "__main__":
    main()
