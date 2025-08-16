from manimlib import *

class HookScene3D(ThreeDScene):
    def construct(self):
        # --- Create the 3D Sky Sphere ---
        sky_sphere = Sphere(radius=100, resolution=(100, 200))
        sky_sphere.flip()

        skybox = TexturedSurface(sky_sphere, "assets/high_res_stars.tif")
        skybox_with_mountain = TexturedSurface(sky_sphere, "assets/high_res_stars_with_mountain.tif")


        # --- Create the Earth ---
        day_texture_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Whole_world_-_land_and_oceans.jpg/1280px-Whole_world_-_land_and_oceans.jpg"
        earth_sphere = Sphere(radius=2, resolution=(100, 200))
        earth = TexturedSurface(earth_sphere, day_texture_url)
        
        # --- Initial Setup ---
        frame = self.camera.frame
        frame.set_euler_angles(theta=10 * DEGREES, phi=80 * DEGREES)
        self.add(skybox, earth)
        earth.add_updater(lambda m, dt: m.rotate(0.05 * dt, axis=UP))
        self.wait(2)
        
        # --- Animations ---
        self.play(frame.animate.set_height(2.5).move_to(RIGHT * 1.5 + OUT * 0.5).increment_theta(-30 * DEGREES), run_time=6)
        earth.clear_updaters()
        self.play(frame.animate.set_height(3.5).move_to(RIGHT * 10).increment_theta(-50 * DEGREES).increment_gamma(60 * DEGREES).increment_phi(10 * DEGREES), run_time=4, rate_func=smooth)
        self.wait(1)
        self.remove(skybox)
        self.add(skybox_with_mountain)
        self.remove(earth)
        self.wait(0.1)
        self.play(frame.animate.increment_gamma(-130*DEGREES), run_time=5)
        self.play(frame.animate.increment_theta(50*DEGREES).shift(-15*UP), run_time=5)
        
        self.wait(1)


class HookScene_End(Scene):
    def construct(self):
        image_path = "videos/HookScene3D.png" # Using forward slash is safer in code

        try:
            background = ImageMobject(image_path)
            background.set_height(FRAME_HEIGHT) # Scale image to fit the screen
            self.add(background)
        except FileNotFoundError:
            error_message = Text(f"ERROR: Still cannot find the image!\nLooked for: {image_path}", color=RED, font_size=36)
            self.add(error_message)
            self.wait(3)
            return

        title = Text("The Journey's End", font_size=72, color=WHITE)
        title.to_edge(UP)

        subtitle = Text("A new perspective.", font_size=48, color=YELLOW)
        subtitle.next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(subtitle, shift=DOWN))
        self.wait(3)