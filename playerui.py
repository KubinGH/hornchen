import math
import pygame

import json_ext as json
from colors import Color
import imglib
from abc_uiwidget import AbstractUIWidget

config_ui = json.load(open("configs/playerui.json"))
minimap_tile = config_ui["minimap_blocksize"]
minimap_tile_t = (minimap_tile, minimap_tile)
minimap_tiles = config_ui["minimap_tiles"]


class MinimapWidget(AbstractUIWidget):
    def __init__(self, game, player):
        super().__init__(game, player)
        full_minimap_size_px = (self.game.vars["mapsize"][0] * minimap_tile, 
                                self.game.vars["mapsize"][1] * minimap_tile)
        self.question_mark = imglib.load_image_from_file("images/sl/QuestionMarkM.png")
        self.background = imglib.repeated_image_texture(self.question_mark, full_minimap_size_px)
        self.full_surface = pygame.Surface(full_minimap_size_px)
        self.surface = pygame.Surface(config_ui["minimap_size"])
        self.rect = self.surface.get_rect()
        self.border = imglib.color_border(config_ui["minimap_size"], (0, 29, 109), 4)

        self.tile_empty = imglib.load_image_from_file("images/dd/env/Bricks.png")
        self.tile_empty = imglib.scale(self.tile_empty, minimap_tile_t)
        self.tile_wall = imglib.load_image_from_file("images/dd/env/WallSmall.png")
        self.tile_wall = imglib.scale(self.tile_wall, minimap_tile_t)
        scaled_player = imglib.scale(self.player.surface, (int(minimap_tile//1.2), int(minimap_tile//1.2)))
        s_rect = scaled_player.get_rect()
        self.tile_current = self.tile_empty.copy()
        self.tile_current.blit(scaled_player, (int((minimap_tile-s_rect.width)//2), int((minimap_tile-s_rect.height)//2)))

    def update_full(self):
        self.full_surface.fill(Color.Black)
        self.full_surface.blit(self.background, (0, 0))
        mazepos = self.game.vars["player_mazepos"]
        for row, irow in enumerate(self.game.vars["maze"]):
            for col, bit in enumerate(irow):
                x, y = col * minimap_tile, row * minimap_tile
                rect = pygame.Rect((x, y), minimap_tile_t)
                if (col, row) == mazepos:
                    tile = self.tile_current
                elif self.player.map_reveal[row][col]:
                    tile = self.tile_wall if bit else self.tile_empty
                else:
                    continue
                self.full_surface.blit(tile, rect)

    def update_part(self):
        mazepos = self.game.vars["player_mazepos"]
        mtopleftidx = ((minimap_tiles[0] - 1)/2 - mazepos[0]), ((minimap_tiles[1] - 1)/2 - mazepos[1])
        mtopleft = mtopleftidx[0] * minimap_tile, mtopleftidx[1] * minimap_tile
        self.rect.topleft = mtopleft
        self.surface.fill(Color.Black)
        self.surface.blit(self.full_surface, self.rect)
        self.surface.blit(self.border, (0, 0))

    def update_on_new_level(self):
        self.update_full()
        self.update_part()

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.surface, config_ui["minimap_pos"])


class HeartsWidget(AbstractUIWidget):
    def __init__(self, game, player):
        super().__init__(game, player)
        self.heart_img = imglib.load_image_from_file("images/sl/Heart.png")
        self.heart_img = imglib.scale(self.heart_img, config_ui["heart_size"])
        self.halfheart_img = imglib.load_image_from_file("images/sl/HeartHalf.png")
        self.halfheart_img = imglib.scale(self.halfheart_img, config_ui["heart_size"])
        self.emptyheart_img = imglib.load_image_from_file("images/sl/HeartEmpty.png")
        self.emptyheart_img = imglib.scale(self.emptyheart_img, config_ui["heart_size"])
        self.last_max_hearts = self.player.max_hearts
        self.heart_surface = self.new_heart_surface()
        self.update_hearts()

    def update(self):
        pass

    def get_hp_half_round(self):
        check = self.player.health_points * 2
        return int(check) / 2 if check % 1 else self.player.health_points

    def new_heart_surface(self):
        hearts = self.player.max_hearts
        heart_size = self.heart_img.get_size()
        width = heart_size[0] * hearts + config_ui["hearts_gap"] * (hearts - 1)
        height = heart_size[1]
        # Don't ask why.
        width += 4; height += 4
        return pygame.Surface((width, height))

    def update_hearts(self):
        if self.player.max_hearts != self.last_max_hearts:
            self.last_max_hearts = self.player.max_hearts
            self.heart_surface = self.new_heart_surface()
        rhealth = self.get_hp_half_round()
        heart_size, gap = config_ui["heart_size"], config_ui["hearts_gap"]
        rect = pygame.Rect(config_ui["hearts_pos"], heart_size)
        drawn = 0
        self.heart_surface.fill(Color.Black)
        for h in range(math.floor(rhealth)):
            self.heart_surface.blit(self.heart_img, rect); drawn += 1
            rect.x += heart_size[0] + gap
        if rhealth % 1 == 0.5:
            self.heart_surface.blit(self.halfheart_img, rect); drawn += 1
            rect.x += heart_size[0] + gap
        for h in range(self.player.max_hearts - drawn):
            self.heart_surface.blit(self.emptyheart_img, rect); drawn += 1
            rect.x += heart_size[0] + gap          

    def update_on_player_damage(self):
        self.update_hearts()

    def draw(self, screen):
        screen.blit(self.heart_surface, config_ui["hearts_pos"])