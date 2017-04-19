import pygame

import fontutils
import imglib
from leveltiles import TileFlags
import json_ext as json
from colors import Color
from basesprite import BaseSprite
import playerui
from libraries import fovlib

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
    base_max_hearts = 3
    base_move_speed = 2
    sprint_move_speed = 6
    base_vision_radius = 16
    def __init__(self, game, *, imgname="Base"):
        self.game = game
        self.current_level = None
        self.rect = pygame.Rect((0, 0), tile_size_t)
        self.image = imglib.load_image_from_file("images/dd/player/Hero{}.png".format(imgname))
        self.image = imglib.scale(self.image, tile_size_t)

        self.moving = {"left": False, "right": False, "up": False, "down": False}
        self.move_sprint = False
        self.going_through_door = False

        self.fov_enabled = self.game.vars["enable_fov"]
        if self.fov_enabled:
            self.computed_fov_map = None
            self.current_level_vision = None

        self.health_points = self.max_hearts # 1 healthpoint == 1 heart

        self.info_font = fontutils.get_font("fonts/BookAntiqua.ttf", config_ui["infofont_size"])
        self.near_passage_text = fontutils.get_text_render(self.info_font, "Press Space to go through the door", True, Color.White)

        self.minimap = playerui.MinimapWidget(self.game, self)
        self.map_reveal = self.new_gamemap_map()
        self.hearts = playerui.HeartsWidget(self.game, self)

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
        pcol, prow = self.closest_tile_index
        inside_level = 0 <= pcol < self.current_level.width and 0 <= prow < self.current_level.height
        for col, row in self.get_tiles_next_to():
            tile = self.current_level.layout[row][col]
            if TileFlags.Passage in tile.flags:
                self.near_passage = tile
                break
        else:
            tile = self.current_level.layout[prow][pcol]
            if TileFlags.Passage in tile.flags:
                self.near_passage = tile
        if self.near_passage is None: 
            self.going_through_door = False
        if self.fov_enabled and inside_level and not self.computed_fov_map[prow][pcol]:
            fovlib.calculate_fov(self.current_level.transparency_map, 
                                 *self.closest_tile_index, self.vision_radius,
                                 dest=self.current_level_vision)
            self.computed_fov_map[prow][pcol] = True

    def draw(self, screen, pos_fix=(0, 0), *, dui=True):
        if self.fov_enabled:
        # Draw black squares in places the player didn't see yet
            for row in self.current_level.layout:
                for tile in row:
                    if not self.current_level_vision[tile.row_idx][tile.col_idx]:
                        rect = pygame.Rect(tile.rect.x + pos_fix[0], tile.rect.y + pos_fix[1], 
                                           tile.rect.width, tile.rect.height)
                        pygame.draw.rect(screen, Color.Black, rect)
        super().draw(screen, pos_fix)
        if dui: self.draw_ui(screen, pos_fix)

    def draw_ui(self, screen, pos_fix=(0, 0)):
        if self.near_passage is not None:
            screen.blit(self.near_passage_text, config_ui["msg_pos"])
        self.minimap.draw(screen)
        self.hearts.draw(screen)

    @property
    def surface(self):
        return self.image

    # ===== Methods =====

    def new_empty_level_map(self):
        return [[False for _ in range(self.current_level.width)]
                for _ in range(self.current_level.height)]

    def new_gamemap_map(self):
        return [[False for _ in range(self.game.vars["mapsize"][0])] 
                for _ in range(self.game.vars["mapsize"][1])]

    def take_damage(self, value):
        self.health_points -= value
        if self.health_points > self.max_hearts:
            self.health_points = self.max_hearts
        
        if value != 0: 
            self.on_damage()

    # Updates

    def on_new_level(self):
        if self.fov_enabled:
            self.computed_fov_map = self.new_empty_level_map()
            self.current_level_vision = self.new_empty_level_map()
        self.reveal_nearby_map_tiles()
        self.minimap.update_on_new_level()

    def on_damage(self):
        self.hearts.update_on_player_damage()

    # Minimap

    def reveal_nearby_map_tiles(self):
        col, row = self.game.vars["player_mazepos"]
        width, height = self.game.vars["mapsize"]
        self.map_reveal[row][col] = True
        for ncol, nrow in [(col+1, row), (col-1, row), (col, row+1), (col, row-1),
                           (col+1, row+1), (col-1, row+1), (col+1, row-1), (col-1, row-1)]:
            if 0 <= ncol < width and 0 <= nrow < height:
                self.map_reveal[nrow][ncol] = True

    def reveal_all_map_tiles(self):
        for row in self.map_reveal:
            for i in range(len(row)):
                row[i] = True

    # ===== Hero attributes =====

    @property
    def move_speed(self):
        if self.move_sprint:
            v = self.sprint_move_speed
        else:
            v = self.base_move_speed
        return v if v < tile_size else tile_size

    @property
    def max_hearts(self):
        return self.base_max_hearts

    @property
    def dying(self):
        return self.health_points < self.max_hearts

    @property
    def vision_radius(self):
        return self.base_vision_radius