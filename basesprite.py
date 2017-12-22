import uuid

import pygame

import json_ext as json
import spriteutils
import utils

print("Load base sprite")

config_dungeon = json.loadf("configs/dungeon.json")
level_size = config_dungeon["level_size"]
tile_size = config_dungeon["tile_size"]
tile_size_t = (tile_size, tile_size)
screen_size = config_dungeon["level_surface_size"]
screen_rect = pygame.Rect((0, 0), screen_size)

def _clamp(number, minim, maxim):
    if number < minim:
        return minim
    if number > maxim:
        return maxim
    else:
        return number

class BaseSprite:
    # TODO: Create Entity base class and remove Entity code in BaseSprite (e.g. health_points, status_effects)
    is_entity = False
    cachable = True
    hostile = False
    friendly = False
    surface = None
    noclip = False
    move_speed = 0
    def __init__(self):
        super().__init__()
        self._id = uuid.uuid4()
        self.rect = None
        self.level = None
        self.moving = {"left": False, "right": False, "up": False, "down": False}
        self.is_overdrawn = False
        self.last_attacked_sprite = None
        self.surface_default = self.surface

    def __hash__(self):
        return hash(self._id)

    def update(self):
        pass
        
    def draw(self, screen, pos_fix=(0, 0)):
        screen.blit(self.surface, self.rect.move(pos_fix))
        nearby = self.get_tiles_next_to() + [self.closest_tile_index]
        self.is_overdrawn = False
        for col, row in nearby:
            tile = self.level.layout[row][col]
            if not tile.transparent and self.rect.colliderect(tile.rect) and \
               (col, row) not in self.level.redrawn:
                self.level.redrawn.add((col, row))
                self.is_overdrawn = True

    def handle_moving(self):
        row, col = self.closest_tile_index
        args = (self.level.layout, self.moving, col, row, 
                self.rect, self.move_speed, screen_rect, self.noclip)
        self.rect, self.collides = spriteutils.move_in_level(*args)

    @property
    def closest_tile_index(self):
        col, row = self.rect.centerx // tile_size, self.rect.centery // tile_size
        # This property is used very often and so we want to speed it up as much as possible
        # function calls reduce speed
        col = 0 if col < 0 else col; col = level_size[0] - 1 if col > level_size[0] - 1 else col
        row = 0 if row < 0 else row; row = level_size[1] - 1 if row > level_size[1] - 1 else row
        # Note: pygame_sdl2 uses float for rect.centerx, so we need a cast
        return int(col), int(row) 

    def get_tiles_next_to(self):
        return spriteutils.get_tiles_next_to(self) 

    @property
    def inside_level(self):
        return self.rect.colliderect(screen_rect)

    def get_collision_nearby(self):
        pcol, prow = self.closest_tile_index
        if not self.level.layout[prow][pcol].passable:
            return True
        for col, row in self.get_tiles_next_to():
            tile = self.level.layout[row][col]
            if not tile.passable and self.rect.colliderect(tile.rect):
                return True
        return False

    def take_damage(self, value):
        self.health_points -= value
        if self.health_points > self.max_health_points:
            self.health_points = self.max_health_points

    def deal_damage(self, sprite):
        sprite.take_damage(self.damage)
        self.last_attacked_sprite = sprite

    def simple_deal_damage(self, once=True):
        for sprite in self.get_local_enemy_sprites():
            if sprite.is_entity and self.rect.colliderect(sprite.rect):
                self.deal_damage(sprite)
                if once:
                    return True
        return False

    @staticmethod
    def get_enemy_sprites_as(friendly, hostile, level):
        result = level.hostile_sprites if friendly else level.friendly_sprites if hostile else []
        result = [s for s in result if s.is_entity]
        if level.parent is not None and hostile:
            result.append(level.parent.player)
        return result

    def get_local_enemy_sprites(self):
        return self.get_enemy_sprites_as(self.friendly, self.hostile, self.level)