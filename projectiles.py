import random

import pygame

import json_ext as json
import imglib
from basesprite import BaseSprite
import utils
import easing

print("Load projectiles")

class TickStatus:
    Ok = 0
    Destroy = 1

# Base

class BaseProjectile(BaseSprite):
    hostile = friendly = False
    cachable = False
    surface = None
    size = (1, 1)
    speed = 3
    damage = 0.5
    def __init__(self, level, pos, *, centerpos=True):
        super().__init__()
        self.level, self.pos = level, pos
        if centerpos:
            self.rect = pygame.Rect((0, 0), self.size)
            self.rect.center = self.pos
        else:
            self.rect = pygame.Rect(self.pos, self.size)

    def destroy(self):
        if self in self.level.sprites:
            self.level.sprites.remove(self)

    def simple_tick(self):
        if not self.inside_level or self.get_collision_nearby() or \
           self.simple_deal_damage(once=True):
            self.destroy()
            return TickStatus.Destroy
        return TickStatus.Ok


# Parents

class SimpleProjectile(BaseProjectile):
    base_size = base_image = image_r = size_r = None
    def __init__(self, level, pos, *, centerpos=True, rotation):
        self.rotation = rotation
        self.surface, self.size = self.image_r[self.rotation], self.size_r[self.rotation]
        super().__init__(level, pos, centerpos=centerpos)

    def update(self):
        if self.rotation == "left":
            self.rect.x -= self.speed
        elif self.rotation == "right":
            self.rect.x += self.speed
        elif self.rotation == "up":
            self.rect.y -= self.speed
        elif self.rotation == "down":
            self.rect.y += self.speed
        if self.simple_tick() is TickStatus.Destroy:
            return


class OmniProjectile(BaseProjectile):
    base_image = None
    speed = 1
    def __init__(self, level, pos, *, centerpos=True, norm_velocity):
        self.norm_velocity = norm_velocity
        self.velocity = self.norm_velocity * self.speed
        self.surface = self.base_image
        self.size = self.surface.get_size()
        super().__init__(level, pos, centerpos=centerpos)
        self.xbuf, self.ybuf = self.rect.topleft

    @classmethod
    def from_angle(cls, level, pos, angle):
        return cls(level, pos, norm_velocity=utils.Vector.from_angle(angle))

    @property
    def velx(self):
        return self.velocity.x
    @property
    def vely(self):
        return self.velocity.y

    def update(self):
        self.xbuf += self.velx
        self.ybuf += self.vely
        self.rect.x, self.rect.y = self.xbuf, self.ybuf
        if self.simple_tick() is TickStatus.Destroy:
            return


class EasedProjectile(BaseProjectile):
    dist = 100
    dist_diff = 20
    length = 100
    def __init__(self, level, pos, *, centerpos=True, norm_vector, ease=easing.ease_quintic_out):
        super().__init__(level, pos, centerpos=centerpos)
        self.norm_vector = norm_vector
        self.ease = ease
        diff = random.randint(-self.dist_diff, self.dist_diff)
        self.move = self.norm_vector * (self.dist + diff) 
        self.ease_args_x = (self.rect.x, self.move.x, self.length)
        self.ease_args_y = (self.rect.y, self.move.y, self.length)
        self.time = 0

    def update(self):
        self.rect.x = self.ease(self.time, *self.ease_args_x)
        self.rect.y = self.ease(self.time, *self.ease_args_y)
        self.time += 1
        if self.time > self.length:
            self.destroy()
            return
        if self.simple_tick() is TickStatus.Destroy:
            return

    def draw(self, screen, fix=(0, 0)):
        screen.blit(self.surface, self.rect.move(fix))

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

class Ember(EasedProjectile):
    hostile = False
    friendly = True
    size = (4, 6)
    surface = imglib.load_image_from_file("images/sl/projectiles/Ember.png", after_scale=size)
    dist = 100
    dist_diff = 20
    length = 100
    damage = 0.25