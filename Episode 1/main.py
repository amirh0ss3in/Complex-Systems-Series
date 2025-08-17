from manimlib import *
from PIL import Image
import os  
import cv2
import numpy as np

Image.MAX_IMAGE_PIXELS = None
manim_config.background = BLACK
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

def add_fractal_detail_recursive(points, roughness, max_iterations):
    """
    A more robust recursive midpoint displacement function.
    It now displaces perpendicularly to the segment connecting the two points.
    """
    if max_iterations == 0:
        return points

    new_points = [points[0]]
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i+1]
        
        midpoint = (p1 + p2) / 2
        
        # Vector from p1 to p2
        vec = p2 - p1
        dist = np.linalg.norm(vec)
        
        if dist < 1e-9: # If points are too close, don't displace
            new_points.append(p2)
            continue
            
        # Perpendicular vector in 2D
        perp_vec = np.array([-vec[1], vec[0], 0])
        
        # Random displacement
        displacement = (np.random.random() - 0.5) * dist * roughness
        
        displaced_midpoint = midpoint + (displacement / np.linalg.norm(perp_vec)) * perp_vec
        
        new_points.append(displaced_midpoint)
        new_points.append(p2)
        
    return add_fractal_detail_recursive(new_points, roughness, max_iterations - 1)


class HookScene_End(Scene):
    def construct(self):
        # ==========================================================
        # PART 1: Trace the "Real" Mountain 
        # ==========================================================
        background_image_path = "videos/HookScene3D.png" 
        mask_image_path = "assets/HookScene3D_edge.png"

        try:
            background = ImageMobject(background_image_path)
            background.set_height(FRAME_HEIGHT)
            self.add(background)
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.add(Text("Error: Background image not found!", color=RED))
            return

        pixel_points, img_width, img_height = get_skyline_from_mask(mask_image_path)
        if not pixel_points:
            print("Failed to get skyline from mask.")
            return

        traced_manim_points = []
        for px, py in pixel_points:
            manim_x = (px / img_width) * FRAME_WIDTH - (FRAME_WIDTH / 2)
            manim_y = (FRAME_HEIGHT / 2) - (py / img_height) * FRAME_HEIGHT
            traced_manim_points.append(np.array([manim_x, manim_y, 0]))

        np.random.seed(42)
        base_points_for_fractal = traced_manim_points[::20] 

        high_res_fractal_points = add_fractal_detail_recursive(base_points_for_fractal, 0.5, 8)
        
        skyline = VMobject(stroke_color=WHITE)
        skyline.set_points_as_corners(high_res_fractal_points)
        skyline.add_updater(lambda m: m.set_stroke(width=2.5 * self.camera.frame.get_width() / FRAME_WIDTH))

        self.play(
            FadeOut(background),
            ShowCreation(skyline),
            run_time=3
        )
        self.wait(1)

        # ==========================================================
        # PART 2: The Zoom
        # ==========================================================
        
        zoom_point = skyline.point_from_proportion(0.7) 

        self.play(
            self.camera.frame.animate.scale(0.1).move_to(zoom_point),
            run_time=5,
            rate_func=linear
        )
        self.wait(2)

        scale_factor = self.camera.frame.get_width() / FRAME_WIDTH

        self.play(skyline.animate.shift(DOWN * scale_factor))

        camera_center = self.camera.frame.get_center()
        fractal_text = Text("Fractal Concepts in Surface Growth", font_size=36, font="Times New Roman").scale(scale_factor).move_to(camera_center + UP * scale_factor)


        frame = self.camera.frame
        center = frame.get_center()
        height = frame.get_height()
        width = frame.get_width()

        bottom_left_corner = center + (LEFT * width / 2) + (10*DOWN * height / 2)
        bottom_right_corner = center + (RIGHT * width / 2) + (10*DOWN * height / 2)

        skyline_points = skyline.get_points()

        polygon_points = list(skyline_points)
        polygon_points.append(bottom_right_corner)
        polygon_points.append(bottom_left_corner)
        
        fill_area = Polygon(
            *polygon_points,
            stroke_width=0,
            fill_color="#7a787b",
            fill_opacity=0.8
        )

        self.add(fill_area)
        self.add(skyline, fractal_text)
        
        self.play(Write(fractal_text), 
                  FadeIn(fill_area))
        self.wait(1)
        self.play(self.camera.frame.animate.shift(DOWN), run_time=2)
        