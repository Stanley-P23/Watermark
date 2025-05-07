from PIL import Image, ImageTk, ImageEnhance
import tkinter as tk
import math
from tkinter import filedialog


class ImageApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Watermarker")
        self.window.minsize(1400, 1000)

        for i in range(10):
            self.window.columnconfigure(i, minsize=140)

        self.center_window()

        self.photo = None
        self.photo_original = None

        self.watermark = None
        self.watermark_original = None

        self.open_button = tk.Button(window, text="Open Image", command=self.open_image, width = 15)
        self.open_button.grid(row=0, column=0, padx=10,pady=10, sticky="W")

        self.watermark_button = tk.Button(window, text="Add Watermark", command=self.add_watermark, width = 15)


        self.save_button = tk.Button(window, text="Save Image", command=self.save_image, width = 15)


        self.image_label = tk.Label(window, bd=0)
        self.image_label.grid(row=1, column=0, columnspan=10)

    def save_image(self):
        if self.photo and self.watermark:

            # Save the image
            save_path = filedialog.asksaveasfilename(defaultextension=".jpg",
                                                     filetypes=[("JPG files", "*.jpg"), ("All files", "*.*")])
            if save_path:
                rgb_image = self.photo.image.convert('RGB')
                rgb_image.save(save_path)

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg;*.jpeg')])
        if file_path:
            self.photo = PhotoImage(file_path, self.image_label)
            self.photo_original = Image.open(file_path)
            self.watermark_button.grid(row=0, column=1, pady=10,  sticky="W")

    def add_watermark(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image Files', '*.png;*.jpg;*.jpeg')])
        if file_path:
            self.watermark = Watermark(file_path, self.window, self.photo.scale)


            self.watermark_original = Image.open(file_path)
            if self.watermark_original.mode != 'RGBA':
                self.watermark_original = self.watermark_original.convert('RGBA')
            self.watermark.edit_overlay()
            self.save_button.grid(row=0, column=2,  pady=10,  sticky="W")

    def display_image(self, img):
        tk_image = ImageTk.PhotoImage(img)
        self.image_label.config(image=tk_image)
        self.image_label.image = tk_image  # Keep a reference

    def update_image_with_watermark(self):
        if self.photo and self.watermark:
            updated_image = self.watermark.apply_to_main_image(self.photo_original.copy())
            self.photo.image = updated_image
            self.photo.scale_image()


    def center_window(self):
        self.window.update_idletasks()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        x_coordinate = (screen_width - window_width) // 2
        y_coordinate = (screen_height - window_height) // 2
        self.window.geometry(f"+{x_coordinate}+{y_coordinate}")

class PhotoImage:
    def __init__(self, file_path, display_label):
        self.file_path = file_path
        self.display_label = display_label
        self.image = Image.open(self.file_path)
        self.scale_image()

    def scale_image(self):
        max_size = 1300
        self.scale = min(max_size / self.image.width, max_size / self.image.height)
        display_size = (int(self.image.width * self.scale), int(self.image.height * self.scale))
        self.image = self.image.resize(display_size, Image.LANCZOS)
        self.display_image()

    def display_image(self):
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.display_label.config(image=self.tk_image)
        self.display_label.image = self.tk_image

class Watermark:
    def __init__(self, file_path, window, photo_scale):
        self.original_scale = 1
        self.scale = 1
        self.transparency = 1.0
        self.tile_spacing = 0  # New attribute for spacing between tiles
        self.tile_mode = 'none'  # New attribute for tiling mode ('none', 'straight', 'diagonal')
        self.position = (0, 0)
        self.file_path = file_path
        self.image = Image.open(self.file_path)
        if self.image.mode != 'RGBA':
            self.image = self.image.convert('RGBA')
        self.window = window
        self.edit_window_open = False
        self.photo_scale = photo_scale
        self.scale_image()

    def scale_image(self):
        watermark_max_size = 300
        self.scale = min(watermark_max_size / self.image.width, watermark_max_size / self.image.height)
        scaled_size = (int(self.image.width * self.scale), int(self.image.height * self.scale))
        self.image = self.image.resize(scaled_size, Image.LANCZOS)

    def apply_tiling(self,
                     main_image):
        # Create a new image that will have the tiled watermark
        tiled_image = Image.new('RGBA', (int(main_image.size[0]*1.3), int(main_image.size[1]*1.3)))

        transparent_watermark = self.set_transparency(self.image, self.transparency)


        for y in range(0, int(main_image.size[1]*1.3), self.image.size[1] + self.tile_spacing):
            for x in range(0, int(main_image.size[0]*1.3), self.image.size[0] + self.tile_spacing):
                if self.tile_mode == 'diagonal' and (y // (self.image.size[1] + self.tile_spacing)) % 2 == 1:
                    # Offset every other row to create the chess tiling effect
                    offset_x = x + (self.image.size[0] + self.tile_spacing) // 2
                else:
                    offset_x = x

                # Make sure the offset does not go outside the main image
                if offset_x < main_image.size[0]*1.25:
                    tiled_image.paste(transparent_watermark, (offset_x, y), self.image)

        # Return the tiled image
        return tiled_image

    def apply_to_main_image(self,
                            main_image):
        # Ensure main_image is in 'RGBA' mode
        if main_image.mode != 'RGBA':
            main_image = main_image.convert('RGBA')

        transparent_image = self.set_transparency(self.image, self.transparency)
        # Ensure transparent_image is in 'RGBA' mode

        main_image.alpha_composite(transparent_image, (self.position[0], self.position[1]))

        if self.tile_mode != 'none':
            # If tiling is enabled, apply tiling first
            tiled_image = self.apply_tiling(main_image)
            # Ensure tiled_image is in 'RGBA' mode

            main_image.alpha_composite(tiled_image, (self.position[0], self.position[1]))



        return main_image

    def set_transparency(self, image, transparency_factor):
        img = image.copy()
        alpha = img.split()[3]
        alpha = ImageEnhance.Brightness(alpha).enhance(transparency_factor)
        img.putalpha(alpha)
        return img



    def edit_overlay(self, event=None):
        if not self.edit_window_open:
            self.edit_window_open = True
            self.edit_window = EditWindow(self, self.close_edit_window, app)

    def close_edit_window(self):
        self.edit_window_open = False
        self.edit_window = None

    def update_position(self, new_position):
        self.position = new_position
        self.edit_overlay()
        app.update_image_with_watermark()

class EditWindow:
    def __init__(self, watermark, on_close_callback, app):
        self.watermark = watermark
        self.on_close_callback = on_close_callback
        self.app = app
        self.edit_window = tk.Toplevel()
        self.edit_window.title("Edit Watermark")
        self.edit_window.protocol("WM_DELETE_WINDOW", self.on_close)
        self.edit_window.minsize(330, 350)
        self.edit_window.columnconfigure(0, weight=1)
        self.edit_window.columnconfigure(1, weight=1)
        self.edit_window.columnconfigure(2, weight=1)

        scale_label = tk.Label(self.edit_window, text="Scale the watermark:")
        scale_label.grid(row=0, column=0, columnspan=3,  pady=(10,0), padx=10)

        self.scale_slider = tk.Scale(self.edit_window, from_=10, to=500, orient='horizontal',  length=200, command=lambda value: self.update_overlay())
        self.scale_slider.set(100)
        self.scale_slider.grid(row=1, column=0,  columnspan=3, padx=10)

        transparency_label = tk.Label(self.edit_window, text="Set transparency:")
        transparency_label.grid(row=2, column=0, columnspan=3,  pady=(25, 0), padx=10)
        self.transparency_slider = tk.Scale(self.edit_window, from_=0, to=100, orient='horizontal',  length=200, command=lambda value: self.update_overlay())
        self.transparency_slider.set(50)
        self.transparency_slider.grid(row=3, column=0, columnspan=3, padx=10, pady=(0, 25))

        # apply_button = tk.Button(self.edit_window, text="Apply Changes", command=self.update_overlay)
        # apply_button.grid(row=4, column=0,  pady=20, padx=10)


        # Tile options as radio buttons
        tales_label = tk.Label(self.edit_window, text="Watermark tiles:")
        tales_label.grid(row=4, column=0, columnspan=3, padx=10)

        self.tile_slider = tk.Scale(self.edit_window, from_=0, to=800, orient='horizontal', length=200,
                                    command=lambda value: self.update_overlay())
        self.tile_slider.set(400)
        self.tile_slider.grid(row=5, column=0, columnspan=3, padx=10, pady=(0, 0))


        self.tile_option = tk.StringVar()
        self.tile_option.set('none')  # default value

        tile_none = tk.Radiobutton(self.edit_window, text="None", variable=self.tile_option, value='none',  command= self.update_overlay)
        tile_none.grid(row=6, column=0)

        tile_straight = tk.Radiobutton(self.edit_window, text="Straight", variable=self.tile_option,
                                       value='straight',  command= self.update_overlay)
        tile_straight.grid(row=6, column=1)

        tile_diagonal = tk.Radiobutton(self.edit_window, text="Diagonal", variable=self.tile_option,
                                       value='diagonal',  command= self.update_overlay)
        tile_diagonal.grid(row=6, column=2)



    def on_close(self):
        self.on_close_callback()
        self.edit_window.destroy()

    def update_overlay(self):
        scale_factor = self.scale_slider.get() / 100.0
        self.watermark.scale = scale_factor
        self.watermark.transparency = self.transparency_slider.get() / 100.0

        # Rescale watermark image
        new_size = (int(self.app.watermark_original.width * scale_factor), int(self.app.watermark_original.height *
                                                                             scale_factor))
        self.watermark.image = self.app.watermark_original.resize(new_size, Image.LANCZOS)
        self.watermark.tile_spacing = self.tile_slider.get()
        self.watermark.tile_mode = self.tile_option.get()
        self.app.update_image_with_watermark()

    def update_tile_spacing(self):
        # This function will be called whenever the tile spacing slider is moved
        self.watermark.tile_spacing = self.tile_slider.get()
        self.app.update_image_with_watermark()


# Mouse dragging functionality
def on_mouse_down(event):
    if app.watermark:
        app.watermark.start_x, app.watermark.start_y = event.x, event.y


def on_mouse_move(event):
    minimum = 20
    if app.watermark:
        dx = event.x - app.watermark.start_x
        dy = event.y - app.watermark.start_y
        distance = math.sqrt(dx ** 2 + dy ** 2)

        # Only update if the mouse has moved more than the minimum distance
        if distance > minimum:
            new_position = (app.watermark.position[0] + dx, app.watermark.position[1] + dy)
            app.watermark.update_position(new_position)
            app.watermark.start_x, app.watermark.start_y = event.x, event.y

root = tk.Tk()
app = ImageApp(root)
root.bind('<ButtonPress-1>', on_mouse_down)
root.bind('<B1-Motion>', on_mouse_move)
root.mainloop()
