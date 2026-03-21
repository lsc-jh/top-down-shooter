from collections.abc import Callable

import pygame
from pygame import Surface
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


Layer = list[list[tuple[int, int]]]


def draw_map(
        screen: Surface,
        tiles: list[Surface],
        layers: list[Layer],
        map_size: tuple[int, int],
        size,
        offset: tuple[int, int] = (0, 0),
        callback: Callable[[int, int, int, int], None] | None = None
) -> None:
    width, height = map_size
    offset_x, offset_y = offset
    for y in range(width):
        for x in range(height):
            draw_x = x * size + offset_x
            draw_y = y * size + offset_y

            for layer in layers:
                if y >= len(layer) or x >= len(layer[y]):
                    continue
                index, rotation = layer[y][x]
                tile = pygame.transform.rotate(tiles[index], -90 * rotation)
                screen.blit(tile, (draw_x, draw_y))

            if callback:
                callback(x, y, draw_x, draw_y)


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
