import uuid

import pygame

import json_ext as json
import spriteutils

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

class BaseSprite(pygame.sprite.Sprite):
    cachable = True
    hostile = False
    friendly = False
    # Used by spriteutils.get_tiles_next_to
    next_to_cache = {}
    surface = None
    move_speed = 0
    def __init__(self):
        super().__init__()
        self._id = uuid.uuid4()
        self.rect = None
        self.level = None
        self.moving = {"left": False, "right": False, "up": False, "down": False}

    def __hash__(self):
        return hash(self._id)

    def update(self):
        pass
        
    def draw(self, screen, pos_fix=(0, 0)):
        screen.blit(self.surface, self.rect.move(pos_fix[0], pos_fix[1]))
        nearby = self.get_tiles_next_to()
        col, row = self.closest_tile_index
        if 0 <= col < level_size[0] and 0 <= row < level_size[1]:
            nearby.append(self.closest_tile_index)
        for col, row in nearby:
            tile = self.level.layout[row][col]
            if tile.passable and not tile.transparent and tile.flags.PartOfHiddenRoom and \
               self.rect.colliderect(tile.rect):
                screen.blit(tile.surface, tile.rect.move(pos_fix[0], pos_fix[1]))

    def handle_moving(self):
        row, col = self.closest_tile_index
        self.rect = spriteutils.move_in_level(self.level.layout, self.moving, col, row, 
                                              self.rect, self.move_speed, screen_rect)

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
        return [(col, row) for col, row in spriteutils.get_tiles_next_to(self) 
                if 0 <= col < level_size[0] and 0 <= row < level_size[1]]

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

    def simple_deal_damage(self, once=True):
        it = self.level.hostile_sprites if self.friendly else self.level.friendly_sprites if self.hostile else []
        for sprite in it:
            if self.rect.colliderect(sprite.rect):
                sprite.take_damage(self.damage)
                if once:
                    return True
        return False