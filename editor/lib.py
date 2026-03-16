from collections.abc import Callable

import pygame
import subprocess
import json
import platform
import os
import sys


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


# TODO: Finish this function to support multiple layers and call the callbacks
def draw_map(
        screen: pygame.Surface,
        map_size: tuple[int, int],
        layers: list[list[list[tuple[int, int]]]],
        tiles: list[pygame.Surface],
        tile_size: int,
        offset: tuple[int, int] = (0, 0),
        on_draw_cells: Callable[list[tuple[int, int]], None] = None,
):
    for row in range(map_size[1]):
        for col in range(map_size[0]):
            x = col * tile_size + offset[0]
            y = row * tile_size + offset[1]
            cells = [layer[row][col] for layer in layers if row < len(layer) and col < len(layer[row])]
            for tile, rotation in cells:
                if tile < len(tiles):
                    image = tiles[tile]
                    if rotation != 0:
                        image = pygame.transform.rotate(image, -90 * rotation)
                    screen.blit(image, (x, y))
            if on_draw_cells and cells:
                on_draw_cells(cells)


def choose_tileset():
    if platform.system() != "Darwin":
        import tkinter as tk
        from tkinter import filedialog
        try:
            root = tk.Tk()
            root.withdraw()
            root.focus_force()

            path = filedialog.askopenfilename(
                title="Select Tileset",
                filetypes=[("Images", "*.png *.jpg *.bmp")]
            )

            return path
        except Exception as e:
            print("Error using tkinter file dialog:", e)
            return None
    else:
        if getattr(sys, "frozen", False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(__file__)

        picker = os.path.join(base, "file_picker.py")

        result = subprocess.run(
            [sys.executable, picker],
            capture_output=True,
            text=True
        )

        raw_json = result.stdout.strip()
        try:
            data = json.loads(raw_json)
            return data.get("path", None)
        except json.JSONDecodeError:
            print("Failed to decode JSON from file picker:", raw_json)
            return None
