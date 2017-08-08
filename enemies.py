import random

import pygame

import imglib
import json_ext as json
from colors import Color
from libraries import spriteutils
from basesprite import BaseSprite
import playeritems # Drops

print("Load enemies")

base_directions = ["left", "right", "up", "down"]

def percent_chance(percent):
    return random.randint(1, 100) <= percent

class BaseEnemy(BaseSprite):
    hostile = True
    hp_bar_gap = 4
    hp_bar_size = (32, 2)
    base_move_speed = 0
    base_damage = 0
    base_max_health_points = 1
    damage_on_player_touch = False
    drops = {}
    def __init__(self, level, spawner_tile):
        super().__init__()
        self.level, self.spawner_tile = level, spawner_tile
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = self.spawner_tile.rect.center
        self.move_speed = self.damage = self.max_health_points = None
        self.reset_attributes()
        self.health_points = self.max_health_points

    def __repr__(self):
        return "<{} @ {}>".format(type(self).__name__, self.rect.topleft)

    def update(self):
        self.reset_attributes()
        player = self.level.parent.player
        if self.damage_on_player_touch and player is not None:
            if self.rect.colliderect(player.rect):
                player.take_damage(self.damage)

        if self.health_points <= 0:
            self.on_death()

    def draw(self, screen, pos_fix=(0, 0)):
        enable_hp_bar = self.level.parent.game.vars["enable_enemy_hp_bars"]
        if enable_hp_bar:
            nearby = self.get_tiles_next_to() + [self.closest_tile_index]
            show_bar = False
            if self.health_points < self.max_health_points:
                for col, row in nearby:
                    tile = self.level.layout[row][col]
                    if tile.passable and tile.flags.PartOfHiddenRoom and not tile.uncovered:
                        break
                else:
                    show_bar = True
            if show_bar:
                pos = self.hp_bar_rect.topleft
                if self.dead:
                    screen.fill(Color.Red, self.hp_bar_rect.move(pos_fix))
                else:
                    px_healthy = min(round(self.health_points / self.max_health_points * self.hp_bar_size[0]), self.hp_bar_size[0])
                    px_damaged = self.hp_bar_size[0] - px_healthy
                    healthy_rect = pygame.Rect(pos, (px_healthy, self.hp_bar_size[1]))
                    screen.fill(Color.Green, healthy_rect.move(pos_fix))
                    if px_damaged:
                        damaged_rect = pygame.Rect((pos[0] + px_healthy, pos[1]), (px_damaged, self.hp_bar_size[1]))
                        screen.fill(Color.Red, damaged_rect.move(pos_fix))
        super().draw(screen, pos_fix)

    def reset_attributes(self):
        self.move_speed = self.base_move_speed
        self.damage = self.base_damage
        self.max_health_points = self.base_max_health_points

    @property
    def hp_bar_rect(self):
        pos = (self.rect.centerx - self.hp_bar_size[0]/2, self.rect.bottom + self.hp_bar_gap)
        return pygame.Rect(pos, self.hp_bar_size)

    def create_cache(self):
        return {
            "type": "enemy",
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

    def on_death(self):
        self.level.sprites.remove(self)
        for dropped_item in self.get_item_drops(self.drops):
            obj = playeritems.DroppedItem(self.level, self.rect.center, dropped_item)
            self.level.sprites.append(obj)

    @staticmethod
    def get_item_drops(dropdict, specifier="any"):
        return []

    def heal(self, value):
        self.take_damage(-value)

    @property
    def dead(self):
        return self.health_points <= 0

class GrayGoo(BaseEnemy):
    base_move_speed = 1
    base_damage = 0.5
    base_max_health_points = 1
    damage_on_player_touch = True
    size = (30, 30)
    surface = imglib.load_image_from_file("images/dd/enemies/GrayGoo.png", after_scale=size)
    def __init__(self, level, spawner_tile):
        super().__init__(level, spawner_tile)
        self.ticks_to_wait = 0
        self.moving = {k: False for k in base_directions}
        self.set_random_move_direction()

    def update(self):
        super().update()
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


class Warlock(BaseEnemy):
    move_speed = 1
    damage = 0.5
    max_health_points = 2
    damage_on_player_touch = True
    size = (30, 30)
    surface = imglib.load_image_from_file("images/dd/enemies/Warlock.png", after_scale=size)
    def __init__(self, level, spawner_tile):
        super().__init__(level, spawner_tile)
        