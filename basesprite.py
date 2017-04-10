import pygame

import json_ext as json
from libraries import spriteutils

config_dungeon = json.load(open("configs/dungeon.json"))
level_size = config_dungeon["level_size"]
tile_size = config_dungeon["tile_size"]
tile_size_t = (tile_size, tile_size)
screen_size = config_dungeon["level_surface_size"]
screen_rect = pygame.Rect((0, 0), screen_size)

class BaseSprite:
    def draw(self, screen, pos_fix=(0, 0)):
        screen.blit(self.surface, (self.rect.x + pos_fix[0], self.rect.y + pos_fix[1]))

    def handle_moving(self):
        row, col = self.closest_tile_index
        self.rect = spriteutils.move_in_level(self.current_level.layout, self.moving, col, row, 
                                              self.rect, self.move_speed, screen_rect)

    def simple_move(self, x, y):
        next_rect = rect_cmove(self.rect, x, y)
        for col, row in self.get_tiles_next_to():
            tile = self.current_level.layout[row][col]
            if not tile.passable and next_rect.colliderect(tile.rect):
                return
        self.rect = next_rect

    @property
    def closest_tile_index(self):
        col, row = self.rect.centerx // tile_size, self.rect.centery // tile_size
        assert 0 <= col < level_size[0]
        assert 0 <= row < level_size[1]
        return col, row

    next_to_cache = {}
    def get_tiles_next_to(self):
        return spriteutils.get_tiles_next_to(self)