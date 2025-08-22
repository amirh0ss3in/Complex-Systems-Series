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
        self.wait(9)
        
        # --- Animations ---
        self.play(frame.animate.set_height(2.5).move_to(RIGHT * 1.25 + OUT * 0.2).increment_theta(-30 * DEGREES), run_time=6)
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
            # Ensure the placeholder text is visible
            self.add(Text("Error: Background image not found!", color=RED).set_z_index(10))
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
            run_time=10,
            rate_func=linear
        )
        self.wait(2)

        scale_factor = self.camera.frame.get_width() / FRAME_WIDTH

        self.play(skyline.animate.shift(DOWN * scale_factor))

        camera_center = self.camera.frame.get_center()
        fractal_text = Text("Self-Affine", font_size=38, font="Times New Roman").scale(scale_factor).move_to(camera_center + UP * scale_factor)
        fractal_text_2 = Text("This is the essence of roughness!", font_size=36, font="Times New Roman").scale(scale_factor).move_to(camera_center + UP * scale_factor)

        self.add(skyline, fractal_text)
        self.play(Write(fractal_text))
        self.wait(1)

        # ==========================================================
        # PART 3: DEFINITION BOX (NEWLY ADDED CODE)
        # ==========================================================
        
        # 1. Create text components for the definition
        word = Text("affine", font="Times New Roman", weight=BOLD, font_size=28)
        pos = Text("(adj.)", font="Times New Roman", font_size=28).next_to(word, RIGHT, buff=0.2)
        definition_text = Text(
            "preserving points, straight lines, and planes.", 
            font="Times New Roman", 
            font_size=24
        ).next_to(word, DOWN, buff=0.2, aligned_edge=LEFT)
        
        # 2. Group text and create a surrounding box
        text_group = VGroup(word, pos, definition_text)
        box = RoundedRectangle(
            corner_radius=0.1,
            stroke_color=WHITE,
            stroke_width=2,
            fill_color=BLACK,
            fill_opacity=0.7
        ).surround(text_group, buff=0.3)

        # 3. Group the box and text, then scale and position it relative to the camera view
        definition_box = VGroup(box, text_group)
        definition_box.scale(scale_factor*0.7)
        definition_box.next_to(fractal_text, RIGHT, buff=scale_factor * 0.5)

        # 4. Animate the definition box
        self.play(FadeIn(definition_box, shift=RIGHT * 0.2 * scale_factor))
        self.wait(5) # Let the audience read the definition
        self.play(FadeOut(definition_box, shift=LEFT * 0.2 * scale_factor))
        self.wait(1)

        # ==========================================================
        # PART 4: Fill the Mountain and Pan Down
        # ==========================================================

        frame = self.camera.frame
        center = frame.get_center()
        height = frame.get_height()
        width = frame.get_width()

        # Extend the bottom corners far down to ensure the fill covers the screen
        bottom_left_corner = center + (LEFT * width / 2) + (10 * DOWN * height / 2)
        bottom_right_corner = center + (RIGHT * width / 2) + (10 * DOWN * height / 2)

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
        
        self.play(
            Transform(fractal_text, fractal_text_2), 
            FadeIn(fill_area)
        )
        self.wait(2)
        self.play(self.camera.frame.animate.shift(DOWN), run_time=2)


class MandelBrot(Scene):
    def construct(self):
        img = ImageMobject("assets/benoit_mandelbrot.jpg", height=5)
        name = Text("Benoit Mandelbrot", font_size=36)
        dates = Text("20 Nov 1924 – 14 Oct 2010", font_size=28)

        # Positioning
        name.next_to(img, DOWN)
        dates.next_to(name, DOWN, buff=0.2)

        # Animations
        self.play(FadeIn(img))
        self.play(img.animate.shift(0.5*UP)) 
        self.play(Write(name), Write(dates))
        self.wait(2)

class SubscribeButton(Scene):
    """
    A Manim scene that animates a cursor moving to and clicking a subscribe button.
    The button then changes state to "Subscribed".

    This scene requires two SVG files in the same directory:
    1. bell.svg - The notification bell icon.
    2. cursor.svg - The hand pointer icon.
    """
    def construct(self):
        # --- Configuration ---
        button_red = "#FF0000"
        subscribed_gray = "#E0E0E0"
        shadow_gray = "#808080"
        button_width = 6.0
        button_height = 1.7
        corner_radius = 0.4
        shadow_offset = 0.08
        click_depth = 0.08

        # --- Create "Subscribe" State Objects ---
        # Button shadow
        button_shadow = RoundedRectangle(
            width=button_width, height=button_height, corner_radius=corner_radius,
            color=shadow_gray, fill_opacity=0.5, stroke_width=0
        ).shift(DOWN * shadow_offset)

        # Main red button shape
        button_rect = RoundedRectangle(
            width=button_width, height=button_height, corner_radius=corner_radius,
            color=button_red, fill_opacity=1, stroke_width=0
        )

        # "SUBSCRIBE" text
        subscribe_text = Text("SUBSCRIBE", font="sans-serif", weight=BOLD, color=WHITE).scale(0.9)
        
        # Bell icon
        bell_icon = SVGMobject("assets/bell.svg").set_color(WHITE).scale(0.35)
        
        # Group text and bell
        button_content = VGroup(subscribe_text, bell_icon).arrange(RIGHT, buff=0.6).move_to(button_rect)
        
        # Group all button elements for the initial state
        subscribe_button = VGroup(button_shadow, button_rect, button_content)

        # --- Create "Subscribed" State Objects ---
        subscribed_rect = button_rect.copy().set_color(subscribed_gray)
        subscribed_text = Text("SUBSCRIBED", font="sans-serif", weight=BOLD, color=BLACK).scale(0.8)
        subscribed_bell = bell_icon.copy().set_color(BLACK)
        subscribed_content = VGroup(subscribed_text, subscribed_bell).arrange(RIGHT, buff=0.4).move_to(subscribed_rect)

        # --- Create Cursor ---
        cursor = SVGMobject("assets/cursor.svg").set_color(WHITE).set_stroke(color=BLACK, width=2).scale(0.45).rotate(15*DEGREES)
        cursor_shadow = cursor.copy().set_fill(shadow_gray, opacity=0.5).set_stroke(width=0)
        cursor_shadow.shift(DOWN * shadow_offset + RIGHT * shadow_offset)
        cursor_group = VGroup(cursor_shadow, cursor)
        
        # Set initial positions
        subscribe_button.move_to(ORIGIN)
        click_position = button_content.get_center() + DOWN * 0.4
        cursor_group.move_to(click_position + DOWN * 2 + RIGHT * 2)

        # --- Animation Sequence ---
        self.add(subscribe_button, cursor_group)
        self.wait(0.5)

        # 1. Move cursor to button
        self.play(cursor_group.animate.move_to(click_position), run_time=1.2, rate_func=smooth)
        self.wait(0.2)

        # 2. Animate the "click down" action
        self.play(
            subscribe_button.animate.shift(DOWN * click_depth),
            cursor_group.animate.shift(DOWN * click_depth),
            run_time=0.1
        )

        # 3. Animate the state change while button is pressed
        self.play(
            Transform(button_rect, subscribed_rect),
            FadeOut(subscribe_text),
            FadeOut(bell_icon),
            FadeIn(subscribed_text),
            FadeIn(subscribed_bell),
            run_time=0.15
        )

        # Group final button state
        subscribed_button_final = VGroup(button_shadow, button_rect, subscribed_content)

        # 4. Animate the "click up" (release) action
        self.play(
            subscribed_button_final.animate.shift(UP * click_depth),
            cursor_group.animate.shift(UP * click_depth),
            run_time=0.1
        )
        self.wait(0.5)

        # 5. Move cursor away
        self.play(cursor_group.animate.shift(DOWN * 1.5 + RIGHT * 2.5), run_time=1.5, rate_func=smooth)
        self.wait(1)
    

class Thumbnail(Scene):
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
            # Ensure the placeholder text is visible
            self.add(Text("Error: Background image not found!", color=RED).set_z_index(10))
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
        self.add(skyline)
        title2 = (
            Text("Hidden Rules of Roughness.", font_size=90, font="Times New Roman")
            .move_to(1.1*UP)
            .set_color("#FFD700")          # Fill color
            .set_stroke(color=BLACK, width=1)  # Outline/stroke
        )
        self.add(title2)
