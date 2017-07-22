import pygame

import json_ext as json
import imglib
from basesprite import BaseSprite
import utils

print("Load projectiles")

# Base

class BaseProjectile(BaseSprite):
    hostile = friendly = False
    cachable = False
    surface = None
    size = (1, 1)
    speed = 3
    damage = 0.5
    def __init__(self, level, pos):
        super().__init__()
        self.level, self.pos = level, pos
        self.rect = pygame.Rect(self.pos, self.size)

    def destroy(self):
        if self in self.level.sprites:
            self.level.sprites.remove(self)

    def simple_tick(self):
        if not self.inside_level or self.get_collision_nearby() or \
           self.simple_deal_damage(once=True):
            self.destroy()
            return True
        return False


# Parents

class SimpleProjectile(BaseProjectile):
    base_size = base_image = image_r = size_r = None
    def __init__(self, level, pos, *, rotation):
        self.rotation = rotation
        self.surface, self.size = self.image_r[self.rotation], self.size_r[self.rotation]
        super().__init__(level, pos)

    def update(self):
        if self.rotation == "left":
            self.rect.x -= self.speed
        elif self.rotation == "right":
            self.rect.x += self.speed
        elif self.rotation == "up":
            self.rect.y -= self.speed
        elif self.rotation == "down":
            self.rect.y += self.speed
        if self.simple_tick():
            return


class OmniProjectile(BaseProjectile):
    base_image = None
    speed = 1
    def __init__(self, level, pos, *, norm_velocity):
        self.norm_velocity = norm_velocity
        self.velocity = self.norm_velocity * self.speed
        self.surface = self.base_image
        self.size = self.surface.get_size()
        # Since pygame.Rect-s use int as fields,
        # we need a buffer that uses floats. Otherwise
        # only some angles will work.
        self.pos_buffer = utils.Vector(pos[0], pos[1])
        super().__init__(level, pos)

    @classmethod
    def from_angle(cls, level, pos, angle):
        return cls(level, pos, norm_velocity=utils.norm_vector_from_angle(angle))

    @property
    def velx(self):
        return self.velocity.x
    @property
    def vely(self):
        return self.velocity.y

    def update(self):
        self.pos_buffer.x += self.velx
        self.pos_buffer.y += self.vely
        self.rect.x, self.rect.y = self.pos_buffer.x, self.pos_buffer.y
        if self.simple_tick():
            return




# Children

class EtherealSword(SimpleProjectile):
    hostile = False
    friendly = True
    base_size = (30, 12)
    base_image = imglib.load_image_from_file("images/sl/projectiles/EtherealSword.png", after_scale=base_size)
    image_r = imglib.all_rotations(base_image)
    size_r = imglib.ValueRotationDependent(*[surface.get_size() for surface in image_r.as_list])
    speed = 3
    damage = 0.5

class Fireball(OmniProjectile):
    hostile = False
    friendly = True
    base_size = (16, 16)
    base_image = imglib.load_image_from_file("images/sl/projectiles/Fireball.png", after_scale=base_size)
    speed = 4
    damage = 0.5
