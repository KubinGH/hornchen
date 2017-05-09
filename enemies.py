import random

import pygame

import imglib
import json_ext as json
from colors import Color
from libraries import spriteutils
from basesprite import BaseSprite

print("Load enemies")

base_directions = ["left", "right", "up", "down"]

#class TileFlags:
#    PartOfHiddenRoom = 3

class BaseEnemy(BaseSprite):
    move_speed = 0
    damage = 0
    max_health_points = 1
    damage_on_player_touch = False
    def __init__(self, level, spawner_tile):
        super().__init__()
        self.level, self.spawner_tile = level, spawner_tile
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = self.spawner_tile.rect.center
        self.health_points = self.max_health_points

    def __repr__(self):
        return "<{} @ {}>".format(type(self).__name__, self.rect.topleft)

    def update(self, player):
        if self.damage_on_player_touch and player is not None:
            if self.rect.colliderect(player.rect):
                player.take_damage(self.damage)

    def create_cache(self):
        return {
            "cls": type(self),
            "rect": self.rect,
            "levelpos": (self.spawner_tile.col_idx, self.spawner_tile.row_idx),
            "health_points": self.health_points
        }

    @classmethod
    def from_cache(cls, level, spawner_tile, cache):
        obj = cls(level, spawner_tile)
        obj.rect = cache["rect"]
        obj.health_points = cache["health_points"]
        return obj

    def take_damage(self, value):
        self.health_points -= value
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points

    def heal(self, value):
        self.health_points += value
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points

class GrayGoo(BaseEnemy):
    move_speed = 1
    damage = 0.5
    max_health_points = 1
    damage_on_player_touch = True
    size = (30, 30)
    surface = imglib.load_image_from_file("images/dd/enemies/GrayGoo.png", after_scale=size)
    def __init__(self, level, spawner_tile):
        super().__init__(level, spawner_tile)
        self.ticks_to_wait = 0
        self.moving = {k: False for k in base_directions}
        self.set_random_move_direction()

    def update(self, player):
        super().update(player)
        last_rect = self.rect
        if not self.ticks_to_wait:
            self.moving[self.direction] = True
            self.handle_moving()
            if self.rect == last_rect:
                self.set_random_move_direction()
        else:
            self.ticks_to_wait -= 1

    def set_random_move_direction(self):
        possible_directions = []
        col, row = self.closest_tile_index
        level_size = self.level.layout_size
        if col > 0 and self.level.layout[row][col - 1].passable:
            possible_directions.append("left")
        if col < level_size[0] - 1 and self.level.layout[row][col + 1].passable:
            possible_directions.append("right")
        if row > 0 and self.level.layout[row - 1][col].passable:
            possible_directions.append("up")
        if row < level_size[1] - 1 and self.level.layout[row + 1][col].passable:
            possible_directions.append("down")
        self.direction = random.choice(possible_directions)

    def create_cache(self):
        cache = super().create_cache()
        cache.update({
            "direction": self.direction
        })
        return cache

    @classmethod
    def from_cache(cls, level, spawner_tile, cache):
        obj = super().from_cache(level, spawner_tile, cache)
        obj.direction = cache["direction"]
        return obj