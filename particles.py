import random

import pygame

import imglib
import utils
import easing

def rotated_square_surface(center, size, angle, color):
    surface = pygame.Surface((size, size))
    surface.fill(color)
    if angle != 0:
        return pygame.transform.rotate(surface, angle).convert_alpha()
    else:
        return surface

class Particle:
    def __init__(self, level, origin, size, 
                 maxvel, length, color, angle=0, rotvel=0,
                 ease=easing.ease_quintic_out):
        self.level = level
        self.origin, self.size = origin, size
        self.maxvel, self.rotvel = maxvel, rotvel
        self.length = length
        self.color, self.angle = color, angle
        self.ease = ease
        self.time = 0
        self.last_angle = angle
        self.last_size = size
        self.ease_args_x = (0, self.maxvel.x, self.length)
        self.ease_args_y = (0, self.maxvel.y, self.length)
        self.surface = self.new_surface()
        self.rect = self.surface.get_rect(); self.rect.center = self.origin
        self.xbuf, self.ybuf = self.origin

    @classmethod
    def from_sprite(cls, sprite, size, maxvel, length, 
                    color, angle=0, rotvel=0, ease=easing.ease_quintic_out):
        origin = sprite.rect.move(random.randint(-7, 7), random.randint(-7, 7)).center
        return cls(sprite.level, origin, size, maxvel, length, color, angle, rotvel, ease)

    def update(self):
        self.time += 1
        self.last_size = self.size
        if self.time >= self.length:
            self.size -= 0.25
            if self.size <= 0:
                self.level.particles.remove(self)
                return
        if int(self.last_angle) != int(self.angle) or self.last_size != self.size:
            self.surface = self.new_surface()
        new_rect = self.surface.get_rect(); new_rect.center = self.rect.center
        self.rect = new_rect
        self.xvel = (self.maxvel.x - self.ease(self.time, *self.ease_args_x))
        self.yvel = (self.maxvel.y - self.ease(self.time, *self.ease_args_y))
        self.xbuf += self.xvel
        self.ybuf += self.yvel
        self.rect.center = (self.xbuf, self.ybuf)

    def draw(self, screen, pos_fix=(0, 0)):
        #screen.blit(self.surface, self.rect.move(pos_fix))
        screen.fill(self.color, self.rect.move(pos_fix))

    def new_surface(self):
        return rotated_square_surface(self.origin, int(self.size), 0, self.color)
