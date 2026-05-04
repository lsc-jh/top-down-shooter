from typing import Callable

import pygame
from pygame import Event
import subprocess
import json
import platform
import os
import sys
from constants import NUMBERS


def get_home_directory():
    if platform.system() == "Windows":
        return os.path.expandvars("%HOMEPATH%")
    else:
        return os.path.expanduser("~")


def get_absolute_path(relative_path):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(__file__)
    return os.path.join(base, relative_path)


def draw_crossed_box(screen, x, y, size, color):
    pygame.draw.rect(screen, color, (x, y, size, size), 1)
    pygame.draw.line(screen, color, (x, y), (x + size, y + size), 1)
    pygame.draw.line(screen, color, (x + size, y), (x, y + size), 1)


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
