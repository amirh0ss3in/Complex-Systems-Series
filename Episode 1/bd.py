from manimlib import *
from random import randint
class BallisticDeposition(Scene):
    def construct(self):
        N_BASE_LINE = 10
        SIDE_LENGTH = 0.8
        base_line = VGroup(*[Square(side_length=SIDE_LENGTH) for _ in range(N_BASE_LINE)]).arrange(RIGHT, buff=0).to_edge(DOWN)
        positions = [square.get_center() for square in base_line]
        dots = VGroup(*[Dot(pos) for pos in positions])
        # random_index_x = randint(0, N_BASE_LINE)
        random_index_x = 5
        square_1 = Square(side_length=SIDE_LENGTH).move_to(positions[random_index_x]+UP*SIDE_LENGTH)
        self.add(dots, square_1, base_line)
        self.play(self.camera.frame.animate.scale(2))
        random_index_x = 4
        square_2 = Square(side_length=SIDE_LENGTH).move_to(positions[random_index_x]+UP*SIDE_LENGTH)
        self.add(square_2)
        


