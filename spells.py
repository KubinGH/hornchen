import random

import pygame

from abc_spell import AbstractSpell
import imglib
import utils
import projectiles

print("Load spells")

def requires_mana(points):
    def wrapper(function):
        def decorated(self, *args, **kwargs):
            if self.player.mana_points >= points:
                self.player.mana_points -= points
                return function(self, *args, **kwargs)
        return decorated
    return wrapper


class Embers(AbstractSpell):
    icon = imglib.load_image_from_file("images/pt/fire-arrows-2.png", after_scale=(32, 32))
    mana_cost = 10
    def __init__(self, player):
        super().__init__(player)

    @requires_mana(mana_cost)
    def cast(self):
        level = self.player.level
        mid_angle = self.player.best_heading_vector.to_angle()
        level = self.player.level
        pos = self.player.rect.center
        count = random.randint(1, 3)
        for i in range(count):
            vec = utils.Vector.from_angle(mid_angle + random.randint(-10, 10))
            projectile = projectiles.Ember(level, pos, norm_vector=vec)
            level.sprites.append(projectile)

