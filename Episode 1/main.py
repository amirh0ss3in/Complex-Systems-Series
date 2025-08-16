from manimlib import *

class HookScene3D(ThreeDScene):
    def construct(self):
        # --- Create the 3D Sky Sphere ---
        sky_sphere = Sphere(radius=100, resolution=(100, 200))
        sky_sphere.flip() # Flip normals to see the texture from the inside

        # NOTE: Make sure you have these files in an 'assets' folder
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
        
        # --- PART 1: The Zoom to Earth ---
        self.play(
            frame.animate.set_height(2.5).move_to(RIGHT * 1.5 + OUT * 0.5).increment_theta(-30 * DEGREES), 
            run_time=2
        )
        earth.clear_updaters()
        
        self.play(
            frame.animate.set_height(3.5).move_to(RIGHT * 10).increment_theta(-50 * DEGREES).increment_gamma(60 * DEGREES).increment_phi(10 * DEGREES),
            run_time=2,
            rate_func=smooth
        )
        self.wait(1)

        # --- PART 2: The Seamless Swap ---
        self.remove(skybox)
        self.add(skybox_with_mountain)
        self.remove(earth)
        self.wait(0.1)
        self.play(frame.animate.increment_gamma(-125*DEGREES).increment_theta(50*DEGREES).shift(10*UP))
        self.embed()
