from manimlib import *
from PIL import Image
import os  
import cv2
import numpy as np

Image.MAX_IMAGE_PIXELS = None

class HookScene3D(ThreeDScene):
    def construct(self):
        # --- Resize Earth Texture (if needed) ---
        original_earth_path = "assets/Whole_world_-_land_and_oceans_12000.jpg"
        resized_earth_path = "assets/resized_earth.jpg"

        # This resizing logic now ONLY runs for the Earth image.
        if not os.path.exists(resized_earth_path):
            print(f"Resizing '{original_earth_path}' to create '{resized_earth_path}'...")
            with Image.open(original_earth_path) as img:
                w, h = img.size
                target_width = 8192 * 2
                target_height = int(target_width * h / w)
                
                resized_img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
                
                # Convert to RGB to save as JPG
                if resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                    
                resized_img.save(resized_earth_path, "jpeg", quality=95)


        # --- Create the 3D Sky Sphere ---
        sky_sphere = Sphere(radius=100, resolution=(100, 200))
        sky_sphere.flip()

        skybox = TexturedSurface(sky_sphere, "assets/high_res_stars.tif")
        skybox_with_mountain = TexturedSurface(sky_sphere, "assets/high_res_stars_with_mountain.tif")


        # --- Create the Earth ---
        earth_sphere = Sphere(radius=2, resolution=(200, 400))
        earth = TexturedSurface(earth_sphere, resized_earth_path)
        
        # --- Initial Setup ---
        frame = self.camera.frame
        frame.set_euler_angles(theta=10 * DEGREES, phi=80 * DEGREES)
        self.add(skybox, earth)
        earth.add_updater(lambda m, dt: m.rotate(0.05 * dt, axis=UP))
        self.wait(2)
        
        # --- Animations ---
        self.play(frame.animate.set_height(2.5).move_to(RIGHT * 1.5 + OUT * 0.5).increment_theta(-30 * DEGREES), run_time=6)
        earth.clear_updaters()
        self.play(frame.animate.set_height(3.5).move_to(RIGHT * 10).increment_theta(-50 * DEGREES).increment_gamma(-70 * DEGREES).increment_phi(10 * DEGREES), run_time=4, rate_func=smooth)
        self.wait(1)
        self.remove(skybox)
        self.add(skybox_with_mountain)
        self.remove(earth)
        self.wait(0.1)
        # self.play(frame.animate.increment_gamma(-130*DEGREES), run_time=5)
        self.play(frame.animate.increment_theta(60*DEGREES).shift(-15*UP), run_time=5)
        
        self.wait(1)

# --- NEW Helper Function for Reading the Edge from a Mask ---
def get_skyline_from_mask(mask_image_path):
    """
    Finds the skyline by reading the first non-white pixel in each column of a mask image.
    This is much more reliable than edge detection if a mask is available.
    
    Returns:
        - A list of (x, y) pixel coordinates for the skyline.
        - The width of the image.
        - The height of the image.
    """
    try:
        # 1. Load the mask image
        image = cv2.imread(mask_image_path)
        if image is None:
            print(f"Error: Could not read mask image at {mask_image_path}")
            return None, None, None
            
        # Convert to grayscale. White will be 255, everything else will be less.
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        img_height, img_width = gray.shape

        # 2. Find the top-most non-white pixel for each column
        skyline_points = []
        # Default to the bottom of the image in case a column is entirely white
        last_y = img_height - 1 

        for x in range(img_width):
            column = gray[:, x]
            # Find the index of the first pixel that is NOT white (value < 255)
            search_result = np.argmax(column < 255)
            
            # If a non-white pixel was found (and it's not the very first pixel of an
            # all-white column), update our y-coordinate.
            if search_result > 0:
                last_y = search_result
            # If the entire column is white, np.argmax returns 0. We check if the
            # pixel at (0,x) is actually part of the mountain. If not, we reuse last_y.
            elif gray[0, x] >= 255: # This column is all white
                pass # last_y is already correct from the previous column
            else: # The mountain starts at the very top of the image in this column
                last_y = 0

            skyline_points.append((x, last_y))

        return skyline_points, img_width, img_height

    except Exception as e:
        print(f"An error occurred during image processing: {e}")
        return None, None, None

class HookScene_End(Scene):
    def construct(self):
        background_image_path = "videos/HookScene3D.png" 
        mask_image_path = "assets/HookScene3D_edge.png"
        try:
            background = ImageMobject(background_image_path)
            background.set_height(FRAME_HEIGHT)
            self.add(background)
        except FileNotFoundError:
            error_message = Text(f"ERROR: Cannot find background image!\nLooked for: {background_image_path}", color=RED, font_size=36)
            self.add(error_message)
            self.wait(3)
            return

        # 1. Get the skyline points from your NEW mask image
        pixel_points, img_width, img_height = get_skyline_from_mask(mask_image_path)

        if not pixel_points:
            print("Could not process the mask image. Exiting animation.")
            return

        # 2. Convert pixel coordinates to Manim coordinates
        manim_points = []
        for px, py in pixel_points:
            manim_x = (px / img_width) * FRAME_WIDTH - (FRAME_WIDTH / 2)
            manim_y = (FRAME_HEIGHT / 2) - (py / img_height) * FRAME_HEIGHT
            manim_points.append(np.array([manim_x, manim_y, 0]))

        # 3. Create and smooth the Manim line
        skyline = VMobject(stroke_color=WHITE, stroke_width=2)
        skyline.set_points_as_corners(manim_points)
        skyline.make_smooth()
        
        
        # 4. Animate the line being drawn
        self.play(
            FadeOut(background),
            ShowCreation(skyline),
            run_time=3
        )

        self.wait(2)