import pygame
import math
import random
import collections

print("Load utilities")

# Angles:
# 0 is right-hand side, increases clockwise

# Vector math


class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return "Vector({}, {})".format(self.x, self.y)

    @classmethod
    def uniform(cls, u):
        return cls(random.uniform(-u, u), random.uniform(-u, u))

    def as_list(self):
        return [self.x, self.y]

    @property
    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalize(self):
        m = self.magnitude
        return Vector(self.x / m, self.y / m)

    def __mul__(self, n):
        if isinstance(n, Vector):
            raise NotImplementedError
        return Vector(self.x * n, self.y * n)

    @classmethod
    def from_angle(cls, angle):
        if   angle == 0:
            return Vector(1, 0)
        elif angle == 90:
            return Vector(0, 1)
        elif angle == 180:
            return Vector(-1, 0)
        elif angle == 360:
            return Vector(0, -1) 
        else:
            radangle = math.radians(angle)
            return Vector(math.cos(radangle), math.sin(radangle))

    def to_angle(self):
        angle = math.degrees(math.atan2(self.y, self.x))
        return angle if angle >= 0 else 360 + angle

# Pygame utilities

def get_pygame_mouse_pos_rect():
    return pygame.Rect(pygame.mouse.get_pos(), (1, 1))

def norm_vector_to_mouse(f, fix=(0, 0)):
    m = get_pygame_mouse_pos_rect().move(fix)
    return Vector(m.x - f[0], m.y - f[1]).normalize()