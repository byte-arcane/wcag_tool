import tkinter as tk
from tkinter import Canvas, Entry, Label, Button, BooleanVar, Checkbutton, Text
from tkinter import colorchooser
import numpy as np
from PIL import Image, ImageTk

"""
Description:
    Visualisation of which colors pass a contrast ratio check, for accessibility purposes
    On the left side, a slice of the color cube is shown, at the slider-provided red value
        The colors shown are ones that pass the contrast test - everything else is transparent
    You can select 1-3 colors for comparing against the color cube colors.
        The associated checkboxes apply the corresponding constraint that the contrast ratio between those colors and the color cube slice should be >= the specified minimum contrast ratio
    You can visualise the colors and the hovered (via mouse) color as foreground/background and vice versa
    
Enjoy!
"""

def rgb_to_hex(rgb):
    return '#%02x%02x%02x'%rgb[:3]

def linear_to_srgb(color):
    return np.where(color <= 0.04045, color / 12.92, ((color + 0.055) / 1.055) ** 2.4)

def luminance(color):
    """Calculate relative luminance of an RGB color"""
    return 0.2126 * color[:,:,0] + 0.7152 * color[:,:,1] + 0.0722 * color[:,:,2]
    
def contrast_ratio_lum(lum1, lum2):
    """Calculate contrast ratio between two RGB colors."""
    l1, l2 = np.maximum(lum1, lum2), np.minimum(lum1, lum2)
    return (l1 + 0.05) / (l2 + 0.05)

class CubeCalc:
    def __init__(self):
        self.lum_bg = None
        
        x = np.arange(256, dtype=np.uint8)
        y = np.arange(256, dtype=np.uint8)
        g, b = np.meshgrid(x, y)
        
        # Precalculate the sRGB luminance of green and blue components (that will remain constant across slices)
        rgb = np.stack((np.full((256, 256), 0, dtype=np.uint8), g, b), axis=-1) / 255.0
        srgb = linear_to_srgb(rgb)
        self.lum_gb = srgb[:,:,1]*0.7152 + srgb[:,:,2]*0.0722
        
    def calc_slice(self, r, min_contrast, color):
        lum_bg = luminance(linear_to_srgb(np.full((256, 256, 3), color, dtype=np.uint8) / 255.0))
        lum = self.lum_gb + 0.2126*linear_to_srgb(r/255.0)
        return (contrast_ratio_lum(lum, lum_bg) >= min_contrast)*255

class NumpyCanvasApp:
    def __init__(self, root, N=2):
        self.root = root
        self.N = N  # Scale factor for pixel replication
        self.contrast_ratio = 3.0
        self.red_index = 0
        self.fg_color = ((255, 255, 255), '#ffffff')
        self.fg2_color = ((0, 255, 0), '#00ff00')
        self.fg3_color = ((255, 0, 0), '#ff0000')
        self.cube_calc = CubeCalc()
        self.data = None
        
        if False:
            x = np.arange(256, dtype=np.uint8) 
            y = np.arange(256, dtype=np.uint8)
            g, b = np.meshgrid(x, y) 
        
        self.canvas_size = 256 * self.N
        self.canvas = Canvas(root, width=self.canvas_size, height=self.canvas_size)
        self.canvas.grid(row=0,column=0)
        
        self.controls_frame = tk.Frame(root)
        self.controls_frame.grid(row=0,column=1)
        
        self.slider_frame = tk.Frame(self.controls_frame)
        self.slider_frame.pack(pady=5)
        Label(self.slider_frame, text="Red value:").grid(row=0, column=0, sticky="w", padx=5)
        self.slider = tk.Scale(self.slider_frame, from_=0, to=256 - 1, orient=tk.HORIZONTAL, command=self.update_image)
        self.slider.grid(row=0, column=1, padx=5)
        
        self.entry_frame = tk.Frame(self.controls_frame)
        self.entry_frame.pack(pady=5)
        Label(self.entry_frame, text="Contrast ratio threshold:").grid(row=0, column=0, sticky="w", padx=5)
        self.entry = Entry(self.entry_frame)
        self.entry.grid(row=0, column=1, padx=5)
        self.entry.insert(0, str(self.contrast_ratio))
        self.entry.bind("<Return>", self.on_entry_change)
        
        self.pixel_info = Label(self.controls_frame, text="Hovered RGB: ")
        self.pixel_info.pack()
        
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        self.c1_frame = tk.Frame(self.controls_frame)
        self.c1_frame.pack(pady=5)
        btn_sel_col_fg = Button(self.c1_frame, text = "Color 1", command = self.choose_fg_color)
        btn_sel_col_fg.grid(row=0, column=0, sticky="w", padx=0)
        self.text1 = Text(self.c1_frame, height = 1, width = 20, fg=self.fg_color[1], font = ("Georgia", 16))
        self.text1.grid(row=0, column=2, sticky="w", padx=0)
        self.text1.insert(1.0, 'Hello World')
        self.text1b = Text(self.c1_frame, height = 1, width = 20, bg=self.fg_color[1], font = ("Georgia", 16))
        self.text1b.grid(row=0, column=3, sticky="w", padx=0)
        self.text1b.insert(1.0, 'Hello World')
        
        self.fg2_checkbox_var = BooleanVar()
        self.fg2_checkbox = Checkbutton(self.c1_frame, text="", variable=self.fg2_checkbox_var, command=self.on_fg2_checkbox_toggle)
        self.fg2_checkbox.grid(row=1,column=1, sticky="w", padx=0)
        btn_sel_col_fg2 = Button(self.c1_frame, text = "Color 2", command = self.choose_fg2_color)
        btn_sel_col_fg2.grid(row=1,column=0, sticky="w", padx=0)
        self.text2 = Text(self.c1_frame, height = 1, width = 20, fg=self.fg2_color[1], font = ("Georgia", 16))
        self.text2.grid(row=1, column=2, sticky="w", padx=0)
        self.text2.insert(1.0, 'Hello World')
        self.text2b = Text(self.c1_frame, height = 1, width = 20, bg=self.fg2_color[1], font = ("Georgia", 16))
        self.text2b.grid(row=1, column=3, sticky="w", padx=0)
        self.text2b.insert(1.0, 'Hello World')
        
        self.fg3_checkbox_var = BooleanVar()
        self.fg3_checkbox = Checkbutton(self.c1_frame, text="", variable=self.fg3_checkbox_var, command=self.on_fg3_checkbox_toggle)
        self.fg3_checkbox.grid(row=2,column=1, sticky="w", padx=0)
        btn_sel_col_fg3 = Button(self.c1_frame, text = "Color 3", command = self.choose_fg3_color)
        btn_sel_col_fg3.grid(row=2,column=0, sticky="w", padx=0)
        self.text3 = Text(self.c1_frame, height = 1, width = 20, fg=self.fg3_color[1], font = ("Georgia", 16))
        self.text3.grid(row=2, column=2, sticky="w", padx=0)
        self.text3.insert(1.0, 'Hello World')
        self.text3b = Text(self.c1_frame, height = 1, width = 20, bg=self.fg3_color[1], font = ("Georgia", 16))
        self.text3b.grid(row=2, column=3, sticky="w", padx=0)
        self.text3b.insert(1.0, 'Hello World')
        
        self.current_image = None
        self.update_image(self.red_index)
        
    def on_fg_checkbox_toggle(self):
        print(f"Checkbox state: {self.fg_checkbox_var.get()}")  
        self.update_image(self.red_index)
        
    def on_fg2_checkbox_toggle(self):
        print(f"Checkbox state: {self.fg2_checkbox_var.get()}") 
        self.update_image(self.red_index)
        
    def on_fg3_checkbox_toggle(self):
        print(f"Checkbox state: {self.fg3_checkbox_var.get()}") 
        self.update_image(self.red_index)
        
    def choose_fg_color(self):
        self.fg_color = colorchooser.askcolor(title ="Choose Color 1") 
        self.update_image(self.red_index)
        print(self.fg_color)
        self.text1.config(fg=self.fg_color[1])
        self.text1b.config(bg=self.fg_color[1])
        
    def choose_fg2_color(self):
        self.fg2_color = colorchooser.askcolor(title ="Choose Color 2") 
        self.update_image(self.red_index)
        print(self.fg_color)
        self.text2.config(fg=self.fg2_color[1])
        self.text2b.config(bg=self.fg2_color[1])
        
    def choose_fg3_color(self):
        self.fg3_color = colorchooser.askcolor(title ="Choose Color 3") 
        self.update_image(self.red_index)
        print(self.fg_color)
        self.text3.config(fg=self.fg3_color[1])
        self.text3b.config(bg=self.fg3_color[1])
    
    def update_image(self, index):
        index = int(index)
        self.red_index = index
        x = np.arange(256, dtype=np.uint8) 
        y = np.arange(256, dtype=np.uint8)
        g, b = np.meshgrid(x, y) 
        self.data = np.zeros((256, 256, 4), dtype=np.uint8)
        self.data[..., :3] =  np.stack((np.full((256, 256), index, dtype=np.uint8), g, b), axis=-1)
        
        mask = self.cube_calc.calc_slice(index,self.contrast_ratio, self.fg_color[0])
        if self.fg2_checkbox_var.get():
            mask = mask & self.cube_calc.calc_slice(index,self.contrast_ratio, self.fg2_color[0])
        if self.fg3_checkbox_var.get():
            mask = mask & self.cube_calc.calc_slice(index,self.contrast_ratio, self.fg3_color[0])
        self.data[:,:,3] = mask
        
        # Resize using nearest-neighbor replication
        img = Image.fromarray(self.data).resize((self.canvas_size, self.canvas_size), Image.NEAREST)
        
        self.current_image = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.current_image)
        
    def on_entry_change(self, event):
        try:
            self.contrast_ratio = float(self.entry.get())
            self.update_image(self.red_index)
        except ValueError:
            pass
            
    def on_mouse_move(self, event):
        x, y = event.x // self.N, event.y // self.N  # Get corresponding pixel in the original 256x256 image
        if 0 <= x < 256 and 0 <= y < 256 and self.data is not None:
            pixel_value = self.data[y, x]  # Get pixel value from the NumPy array
            self.pixel_info.config(text=f"Pixel Value: {tuple(pixel_value)}")
            
            rgbhex = rgb_to_hex(tuple(pixel_value))
            self.text1.config(bg=rgbhex)
            self.text1b.config(fg=rgbhex)
            self.text2.config(bg=rgbhex)
            self.text2b.config(fg=rgbhex)
            self.text3.config(bg=rgbhex)
            self.text3b.config(fg=rgbhex)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("WCAG color cube contrast tool")
    app = NumpyCanvasApp(root, N=2)
    root.mainloop()
