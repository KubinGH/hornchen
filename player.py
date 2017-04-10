import pygame

import fontutils
import imglib
from leveltiles import TileFlags
import json_ext as json
from colors import Color
from basesprite import BaseSprite

from libraries import spriteutils

config_dungeon = json.load(open("configs/dungeon.json"))
level_size = config_dungeon["level_size"]
tile_size = config_dungeon["tile_size"]
tile_size_t = (tile_size, tile_size)
screen_size = config_dungeon["level_surface_size"]
screen_rect = pygame.Rect((0, 0), screen_size)

config_ui = json.load(open("configs/playerui.json"))
minimap_tile = config_ui["minimap_blocksize"]
minimap_tiles = config_ui["minimap_tiles"]

class PlayerCharacter(BaseSprite):
    base_move_speed = 2
    sprint_move_speed = 6
    def __init__(self, game, *, imgname="Base"):
        self.game = game
        self.current_level = None
        self.rect = pygame.Rect((0, 0), tile_size_t)
        self.image = imglib.load_image_from_file("images/dd/player/Hero{}.png".format(imgname))
        self.image = imglib.scale(self.image, tile_size_t)

        self.moving = {"left": False, "right": False, "up": False, "down": False}
        self.move_sprint = False
        self.going_through_door = False

        self.info_font = fontutils.get_font("fonts/BookAntiqua.ttf", config_ui["infofont_size"])
        self.near_passage_text = fontutils.get_text_render(self.info_font, "Press Space to go through the door", True, Color.White)

        self.full_minimap_surface = pygame.Surface((level_size[0] * tile_size, level_size[1] * tile_size))
        self.minimap_surface = pygame.Surface(config_ui["minimap_size"])
        self.minimap_rect = self.minimap_surface.get_rect()
        self.minimap_border = imglib.color_border(config_ui["minimap_size"], (0, 29, 109), 4)

    def handle_events(self, events, pressed_keys, mouse_pos):
        self.moving["left"]  = pressed_keys[pygame.K_LEFT]
        self.moving["right"] = pressed_keys[pygame.K_RIGHT]
        self.moving["up"]    = pressed_keys[pygame.K_UP]
        self.moving["down"]  = pressed_keys[pygame.K_DOWN]
        self.move_sprint     = pressed_keys[pygame.K_s]
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.going_through_door = True


    def update(self):
        self.handle_moving()
        self.near_passage = None
        for col, row in self.get_tiles_next_to():
            tile = self.current_level.layout[row][col]
            if TileFlags.Passage in tile.flags:
                self.near_passage = tile
                break
        else:
            col, row = self.closest_tile_index
            tile = self.current_level.layout[row][col]
            if TileFlags.Passage in tile.flags:
                self.near_passage = tile
        if self.near_passage is None: 
            self.going_through_door = False

    def draw(self, screen, pos_fix=(0, 0)):
        super().draw(screen, pos_fix)
        if self.near_passage is not None:
            screen.blit(self.near_passage_text, (10, pos_fix[1] - 35))
        screen.blit(self.minimap_surface, config_ui["minimap_pos"])

    @property
    def surface(self):
        return self.image

    # ===== Methods =====

    def on_new_level(self):
        self.update_full_minimap()
        self.update_minimap()

    def update_full_minimap(self):
        mazepos = self.game.vars["player_mazepos"]
        for row, irow in enumerate(self.game.vars["maze"]):
            for col, bit in enumerate(irow):
                x, y = col * minimap_tile, row * minimap_tile
                rect = pygame.Rect(x, y, minimap_tile, minimap_tile)
                if bit:
                    color = Color.Black
                else:
                    if (col, row) == mazepos:
                        color = Color.Yellow
                    else:
                        color = Color.White
                pygame.draw.rect(self.full_minimap_surface, color, rect)

    def update_minimap(self):
        mazepos = self.game.vars["player_mazepos"]
        mtopleftidx = ((minimap_tiles[0] - 1)/2 - mazepos[0]), ((minimap_tiles[1] - 1)/2 - mazepos[1])
        mtopleft = mtopleftidx[0] * minimap_tile, mtopleftidx[1] * minimap_tile
        self.minimap_rect.topleft = mtopleft
        self.minimap_surface.fill(Color.Black)
        self.minimap_surface.blit(self.full_minimap_surface, self.minimap_rect)
        self.minimap_surface.blit(self.minimap_border, (0, 0))


    # ===== Hero attributes =====

    @property
    def move_speed(self):
        if self.move_sprint:
            v = self.sprint_move_speed
        else:
            v = self.base_move_speed
        return v if v < tile_size else tile_size


if __name__ == "__main__":
    pygame.init()
    p = PlayerCharacter(object())