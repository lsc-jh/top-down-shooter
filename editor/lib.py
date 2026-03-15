import pygame
import subprocess
import json


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


import subprocess
import os
import sys


def choose_tileset():
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
