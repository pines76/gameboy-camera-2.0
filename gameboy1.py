#!/usr/bin/env python3


import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import tempfile
import os

# --------------------
# Palettes
# --------------------
PALETTES = {
    "Greyscale": ["#141414", "#545454", "#949494", "#d4d4d4"],
    "Classic Green": ["#405010", "#708028", "#a0a840", "#d0d058"],
    "Monochrome Blue": ["#081820", "#346856", "#88c070", "#e0f8cf"],

    "Ice Cream": ["#7c3f58", "#eb6b6f", "#f9a875", "#fff6d3"],
    "Metallic": ["#221e31", "#41485d", "#778e98", "#c5dbd4"],
    "Earth": ["#774346", "#b87652", "#ecb965", "#f5f29e"],
    "Kirby": ["#2c2c96", "#7733e7", "#e78686", "#f7bef7"],
    "Spaghetti": ["#141414", "#da7381", "#fbe2a2", "#d4d4d4"],
    "Space Haze": ["#0b0b30", "#6b1fb1", "#cc3495", "#f8e3c4"],
    "Pumpkin": ["#142b23", "#19692c", "#e06e16", "#f7db7e"],
    "Hollow": ["#0f0f1b", "#565a75", "#c6b7be", "#fafbf6"],
    "Purple Dawn": ["#001b2e", "#2d75be", "#9a7bbc", "#eefded"],
    "Coffee": ["#564438", "#937369", "#d2bba0", "#f2efc7"],
    "Rustic": ["#2c2137", "#764462", "#a96868", "#edb4a1"],
    "Mist": ["#2d1600", "#1e606e", "#5ab9a8", "#c4f0c2"],
}

# --------------------
# App
# --------------------
class GameBoyCameraApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Boy Camera Effect")
        self.root.geometry("520x520")
        self.root.resizable(False, False)

        self.palette_var = tk.StringVar(value="Classic Green")
        self.brightness = tk.DoubleVar(value=0)
        self.contrast = tk.DoubleVar(value=0)
        self.crop_square = tk.BooleanVar(value=False)

        # Grid layout
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        # Controls
        controls = tk.Frame(root)
        controls.grid(row=0, column=0, sticky="ew", pady=6)

        tk.Label(controls, text="Palette").pack()
        tk.OptionMenu(
            controls,
            self.palette_var,
            *PALETTES.keys(),
            command=self.update_preview
        ).pack()

        tk.Label(controls, text="Brightness").pack(pady=(4,0))
        tk.Scale(
            controls,
            from_=-50,
            to=50,
            orient="horizontal",
            variable=self.brightness,
            command=self.update_preview,
            length=300
        ).pack()

        tk.Label(controls, text="Contrast").pack(pady=(4,0))
        tk.Scale(
            controls,
            from_=-50,
            to=50,
            orient="horizontal",
            variable=self.contrast,
            command=self.update_preview,
            length=300
        ).pack()

        tk.Checkbutton(
            controls,
            text="Crop to Square",
            variable=self.crop_square,
            command=self.update_preview
        ).pack(pady=4)

        tk.Button(
            controls,
            text="Select Image",
            command=self.select_image
        ).pack(pady=4)

        # Preview area
        self.preview_frame = tk.Frame(root)
        self.preview_frame.grid(row=3, column=0, sticky="nsew")

        self.preview_label = tk.Label(self.preview_frame)
        self.preview_label.pack(expand=True)

        # Save button pinned to bottom
        self.btn_save = tk.Button(
            root,
            text="Save Image",
            command=self.save_image,
            state="disabled"
        )
        self.btn_save.grid(row=4, column=0, pady=8)

        self.input_path = None
        self.tk_img = None

    # --------------------
    # Image selection
    # --------------------
    def select_image(self):
        self.input_path = filedialog.askopenfilename(
            title="Select an image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not self.input_path:
            return

        self.btn_save.config(state="normal")
        self.update_preview()

    # --------------------
    # Crop to square helper
    # --------------------
    def crop_image_to_square(self, path):
        img = Image.open(path)
        width, height = img.size
        min_edge = min(width, height)
        left = (width - min_edge)//2
        top = (height - min_edge)//2
        right = left + min_edge
        bottom = top + min_edge
        cropped_path = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        img.crop((left, top, right, bottom)).save(cropped_path)
        return cropped_path

    # --------------------
    # Preview
    # --------------------
    def update_preview(self, *_):
        if not self.input_path:
            return

        palette = PALETTES[self.palette_var.get()]
        temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        temp_palette = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

        # Possibly crop first
        working_path = self.input_path
        if self.crop_square.get():
            working_path = self.crop_image_to_square(self.input_path)

        brightness = int(self.brightness.get())
        contrast = int(self.contrast.get())

        try:
            # Palette file
            palette_cmd = ["convert", "-size", "4x1", "xc:none"]
            for i, color in enumerate(palette):
                palette_cmd += ["-fill", color, "-draw", f"point {i},0"]
            palette_cmd.append(temp_palette)
            subprocess.run(palette_cmd, check=True)

            cmd = [
                "convert",
                working_path,
                "-filter", "point",
                "-resize", "160x144",
                "-colorspace", "Gray",
                "-brightness-contrast", f"{brightness}x{contrast}",
                "-ordered-dither", "o4x4,4",
                "-colors", "4",
                "-resize", "320x288",
                "-remap", temp_palette,
                temp_out
            ]
            subprocess.run(cmd, check=True)

            img = Image.open(temp_out)
            img.thumbnail((280, 220), Image.NEAREST)
            self.tk_img = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.tk_img)

        finally:
            for f in (temp_out, temp_palette):
                if os.path.exists(f):
                    os.remove(f)
            if self.crop_square.get() and working_path != self.input_path:
                os.remove(working_path)

    # --------------------
    # Save
    # --------------------
    def save_image(self):
        output_path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )
        if not output_path:
            return

        palette = PALETTES[self.palette_var.get()]
        temp_palette = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name

        # Possibly crop
        working_path = self.input_path
        if self.crop_square.get():
            working_path = self.crop_image_to_square(self.input_path)

        brightness = int(self.brightness.get())
        contrast = int(self.contrast.get())

        try:
            # Palette
            palette_cmd = ["convert", "-size", "4x1", "xc:none"]
            for i, color in enumerate(palette):
                palette_cmd += ["-fill", color, "-draw", f"point {i},0"]
            palette_cmd.append(temp_palette)
            subprocess.run(palette_cmd, check=True)

            # Save at 148x144
            cmd = [
                "convert",
                working_path,
                "-filter", "point",
                "-resize", "148x144!",
                "-colorspace", "Gray",
                "-brightness-contrast", f"{brightness}x{contrast}",
                "-ordered-dither", "o4x4,4",
                "-colors", "4",
                "-remap", temp_palette,
                output_path
            ]
            subprocess.run(cmd, check=True)

            messagebox.showinfo("Success", "Image saved successfully.")

        finally:
            for f in (temp_palette,):
                if os.path.exists(f):
                    os.remove(f)
            if self.crop_square.get() and working_path != self.input_path:
                os.remove(working_path)

# --------------------
# Run
# --------------------
if __name__ == "__main__":
    root = tk.Tk()
    GameBoyCameraApp(root)
    root.mainloop()
