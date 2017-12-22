import random

import pygame

from basesprite import BaseSprite
import imglib
import utils
import easing

print("Load particles")

# Slowdown - start maximum, end 0
_summer = easing.ease_value_sum_fm
# Speedup - start 0, end maximum (use with ease in-out or in)
_summer2 = easing.ease_value_sum

class Particle(BaseSprite):
    def __init__(self, level, origin, size, 
                 maxvel_or_dist, length, color, *, angle=0, rotvel=0,
                 ease=easing.ease_quintic_out, from_dist=False,
                 length_disperse=0.3):
        self.level = level
        self.origin, self.size = origin, size
        if length_disperse > 0:
            length *= 1 + random.uniform(-length_disperse, length_disperse)
            length = round(length)
            if length == 0: length = 1
        self.length = length
        self.color, self.angle, self.rotvel = color, angle, rotvel
        self.ease = ease
        self.time = 0
        self.last_angle = angle
        self.last_size = size
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.rect.center = self.origin
        if not from_dist:
            self.maxvel = maxvel_or_dist
            self.ease_args_x_fv = (0, self.maxvel.x, self.length)
            self.ease_args_y_fv = (0, self.maxvel.y, self.length)
            app = self.length // 100 if self.length >= 100 else 1
            sumx = _summer(self.ease, self.maxvel.x, *self.ease_args_x_fv, app=app)
            sumy = _summer(self.ease, self.maxvel.y, *self.ease_args_y_fv, app=app)
            self.dist = utils.Vector(sumx, sumy)
        else:
            self.maxvel = None
            self.dist = maxvel_or_dist
        self.ease_args_x = (self.origin[0], self.dist.x, self.length)
        self.ease_args_y = (self.origin[1], self.dist.y, self.length)

    @classmethod
    def from_sprite(cls, sprite, size, maxvel_or_dist, length, 
                    color, *, angle=0, rotvel=0, ease=easing.ease_quintic_out, from_dist=False):
        origin = sprite.rect.move(random.randint(-7, 7), random.randint(-7, 7)).center
        return cls(sprite.level, origin, size, maxvel_or_dist, length, color, 
                   angle=angle, rotvel=rotvel, ease=ease, from_dist=from_dist)

    def update(self):
        self.time += 1
        self.last_size = self.size
        if self.time >= self.length:
            self.size -= 0.25
            if self.size <= 0:
                self.level.particles.remove(self)
                return
        if self.last_size != self.size and not self.size % 1:
            new_rect = pygame.Rect(0, 0, self.size, self.size)
            new_rect.center = self.rect.center
            self.rect = new_rect
        if self.ease == easing.ease_quintic_out:
            x = self.dist.x * ((self.time / self.length - 1) ** 5 + 1) + self.origin[0]
            y = self.dist.y * ((self.time / self.length - 1) ** 5 + 1) + self.origin[1]
        else:
            x = self.ease(self.time, *self.ease_args_x)
            y = self.ease(self.time, *self.ease_args_y)
        self.rect.center = (x, y)

    def draw(self, screen, pos_fix=(0, 0)):
        screen.fill(self.color, self.rect.move(pos_fix))        
        nearby = self.get_tiles_next_to() + [self.closest_tile_index]
        for col, row in nearby:
            tile = self.level.layout[row][col]
            if not tile.transparent and self.rect.colliderect(tile.rect) and \
               (col, row) not in self.level.redrawn:
                self.level.redrawn.add((col, row))