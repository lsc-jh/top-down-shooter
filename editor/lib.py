import pygame
import subprocess
import json
import platform
import os
import sys


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
