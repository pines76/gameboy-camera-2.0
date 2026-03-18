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
        self.root.geometry("520x650")
        self.root.resizable(False, False)

        # Frames
        controls_frame = tk.Frame(root)
        controls_frame.pack(fill="x", pady=5)

        preview_frame = tk.Frame(root, width=300, height=240, bg="black")
        preview_frame.pack(pady=10)
        preview_frame.pack_propagate(False)

        # Variables
        self.palette_var = tk.StringVar(value="Classic Green")
        self.brightness = tk.DoubleVar(value=0)
        self.contrast = tk.DoubleVar(value=0)
        self.crop_square = tk.BooleanVar(value=False)
        self.keep_size = tk.BooleanVar(value=False)
        self.keep_color = tk.BooleanVar(value=False)
        self.sensor_grid = tk.BooleanVar(value=False)
        self.gb_contrast = tk.BooleanVar(value=False)

        # --------------------
        # Controls
        # --------------------
        tk.Label(controls_frame, text="Palette").pack()
        tk.OptionMenu(
            controls_frame,
            self.palette_var,
            *PALETTES.keys(),
            command=self.update_preview
        ).pack()

        tk.Label(controls_frame, text="Brightness").pack()
        tk.Scale(
            controls_frame,
            from_=-50,
            to=50,
            orient="horizontal",
            variable=self.brightness,
            command=self.update_preview,
            length=300
        ).pack()

        tk.Label(controls_frame, text="Contrast").pack()
        tk.Scale(
            controls_frame,
            from_=-50,
            to=50,
            orient="horizontal",
            variable=self.contrast,
            command=self.update_preview,
            length=300
        ).pack()

        tk.Checkbutton(
            controls_frame,
            text="Crop to Square",
            variable=self.crop_square,
            command=self.update_preview
        ).pack()

        tk.Checkbutton(
            controls_frame,
            text="Keep Original Size",
            variable=self.keep_size,
            command=self.update_preview
        ).pack()

        tk.Checkbutton(
            controls_frame,
            text="Keep Original Colours (Dither Only)",
            variable=self.keep_color,
            command=self.update_preview
        ).pack()

        tk.Checkbutton(
            controls_frame,
            text="Simulate Sensor Grid",
            variable=self.sensor_grid,
            command=self.update_preview
        ).pack()

        tk.Checkbutton(
            controls_frame,
            text="Game Boy Contrast Curve",
            variable=self.gb_contrast,
            command=self.update_preview
        ).pack()

        # Buttons side-by-side
        btn_frame = tk.Frame(controls_frame)
        btn_frame.pack(pady=5)

        tk.Button(
            btn_frame,
            text="Select Image",
            command=self.select_image
        ).pack(side="left", padx=5)

        self.btn_save = tk.Button(
            btn_frame,
            text="Save Image",
            command=self.save_image,
            state="disabled"
        )
        self.btn_save.pack(side="left", padx=5)

        # Preview
        self.preview_label = tk.Label(preview_frame, bg="black")
        self.preview_label.pack(expand=True)

        self.input_path = None
        self.tk_img = None

    # --------------------
    def select_image(self):
        self.input_path = filedialog.askopenfilename(
            filetypes=[("Images","*.png *.jpg *.jpeg *.bmp")]
        )
        if not self.input_path:
            return
        self.btn_save.config(state="normal")
        self.update_preview()

    # --------------------
    def build_command(self, output):

        brightness = int(self.brightness.get())
        contrast = int(self.contrast.get())
        cmd = ["convert", self.input_path]

        temp_palette = None

        # Fixed square crop
        if self.crop_square.get():
            img = Image.open(self.input_path)
            w, h = img.size
            size = min(w, h)
            x = (w - size) // 2
            y = (h - size) // 2

            cmd += [
                "-crop", f"{size}x{size}+{x}+{y}",
                "+repage"
            ]

        # Resize
        if self.keep_size.get():
            cmd += ["-resize","25%","-filter","point"]
        else:
            cmd += ["-resize","160x144","-filter","point"]

        if self.gb_contrast.get():
            cmd += ["-sigmoidal-contrast","8,45%"]

        cmd += ["-brightness-contrast", f"{brightness}x{contrast}"]

        if self.keep_color.get():
            cmd += ["-ordered-dither","o4x4,4"]
        else:
            cmd += ["-colorspace","Gray","-ordered-dither","o4x4,4","-colors","4"]

            palette = PALETTES[self.palette_var.get()]
            temp_palette = tempfile.NamedTemporaryFile(delete=False,suffix=".png").name

            palette_img = Image.new("RGB",(4,1))
            for i,color in enumerate(palette):
                palette_img.putpixel((i,0),
                    tuple(int(color[j:j+2],16) for j in (1,3,5)))
            palette_img.save(temp_palette)

            cmd += ["-remap",temp_palette]

        if self.keep_size.get():
            cmd += ["-resize","400%"]
        else:
            cmd += ["-resize","320x288"]

        if self.sensor_grid.get():
            cmd += [
                "(",
                "-size","2x2",
                "pattern:checkerboard",
                "-alpha","set",
                "-channel","A",
                "-evaluate","set","15%",
                ")",
                "-compose","overlay",
                "-composite"
            ]

        cmd.append(output)

        return cmd, temp_palette

    # --------------------
    def update_preview(self, *_):
        if not self.input_path:
            return

        temp_out = tempfile.NamedTemporaryFile(delete=False,suffix=".png").name

        try:
            cmd, temp_palette = self.build_command(temp_out)
            subprocess.run(cmd,check=True)

            img = Image.open(temp_out)
            img.thumbnail((300, 240), Image.NEAREST)

            self.tk_img = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.tk_img)

        finally:
            if os.path.exists(temp_out):
                os.remove(temp_out)
            if temp_palette and os.path.exists(temp_palette):
                os.remove(temp_palette)

    # --------------------
    def save_image(self):
        output = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG","*.png")]
        )
        if not output:
            return

        cmd, temp_palette = self.build_command(output)
        subprocess.run(cmd,check=True)

        if temp_palette and os.path.exists(temp_palette):
            os.remove(temp_palette)

        messagebox.showinfo("Saved","Image saved successfully.")

# --------------------
if __name__ == "__main__":
    root = tk.Tk()
    GameBoyCameraApp(root)
    root.mainloop()