import pygame
from tkinter import filedialog


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


def choose_tileset():
    root = filedialog.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select Tileset Image",
        filetypes=[("Image Files", "*.png;*.jpg;*.bmp")]
    )
    return file_path
