import tkinter as tk
from tkinter import filedialog
import json

root = tk.Tk()
# Hide the main window
root.withdraw()
root.focus_force()


path = filedialog.askopenfilename(
    title="Select Tileset",
    filetypes=[("Images", "*.png *.jpg *.bmp")]
)

print(json.dumps({"path": path}))
