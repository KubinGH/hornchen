import pygame

import json_ext as json
from libraries import spriteutils
from leveltiles import TileFlags

print("Load base sprite")

config_dungeon = json.load(open("configs/dungeon.json"))
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
    # Used by spriteutils.get_tiles_next_to
    next_to_cache = {}
    def draw(self, screen, pos_fix=(0, 0)):
        screen.blit(self.surface, self.rect.move(pos_fix[0], pos_fix[1]))
        nearby = self.get_tiles_next_to() + [self.closest_tile_index]
        for col, row in nearby:
            tile = self.level.layout[row][col]
            if tile.passable and not tile.transparent and self.rect.colliderect(tile.rect) and \
                    TileFlags.PartOfHiddenRoom in tile.flags:
                screen.blit(tile.surface, tile.rect.move(pos_fix[0], pos_fix[1]))

    def handle_moving(self):
        row, col = self.closest_tile_index
        self.rect = spriteutils.move_in_level(self.level.layout, self.moving, col, row, 
                                              self.rect, self.move_speed, screen_rect)

    def handle_simple_moving(self, x, y):
        next_rect = rect_cmove(self.rect, x, y)
        for col, row in self.get_tiles_next_to():
            tile = self.current_level.layout[row][col]
            if not tile.passable and next_rect.colliderect(tile.rect):
                return
        self.rect = next_rect

    @property
    def closest_tile_index(self):
        col, row = self.rect.centerx // tile_size, self.rect.centery // tile_size
        col = _clamp(col, 0, level_size[0])
        row = _clamp(row, 0, level_size[1])
        return col, row

    def get_tiles_next_to(self):
        return spriteutils.get_tiles_next_to(self)