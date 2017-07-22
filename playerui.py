import math
import pygame

import json_ext as json
from colors import Color
import imglib
from abc_uiwidget import AbstractUIWidget

print("Load player UI")

config_ui = json.loadf("configs/playerui.json")
minimap_tile = config_ui["minimap_blocksize"]
minimap_tile_t = (minimap_tile, minimap_tile)
minimap_tiles = config_ui["minimap_tiles"]


class MinimapWidget(AbstractUIWidget):
    question_mark = imglib.load_image_from_file("images/sl/minimap/QuestionMarkM.png", after_scale=minimap_tile_t)
    tile_empty = imglib.load_image_from_file("images/dd/env/Bricks.png", after_scale=minimap_tile_t)
    tile_wall = imglib.load_image_from_file("images/dd/env/WallSmall.png", after_scale=minimap_tile_t)
    def __init__(self, game, player):
        super().__init__(game, player)
        full_minimap_size_px = (self.game.vars["mapsize"][0] * minimap_tile, 
                                self.game.vars["mapsize"][1] * minimap_tile)
        self.background = imglib.repeated_image_texture(self.question_mark, full_minimap_size_px)
        self.full_surface = pygame.Surface(full_minimap_size_px)
        self.surface = pygame.Surface(config_ui["minimap_size"])
        self.rect = self.surface.get_rect()
        self.border = imglib.color_border(config_ui["minimap_size"], (0, 29, 109), 4, nowarn=True)
        mini_player_size = (int(minimap_tile/1.2), int(minimap_tile/1.2))
        scaled_player = imglib.scale(self.player.surface, mini_player_size)
        s_rect = scaled_player.get_rect()
        self.tile_current = self.tile_empty.copy()
        mini_player_pos = (int((minimap_tile-s_rect.width)/2), int((minimap_tile-s_rect.height)/2))
        self.tile_current.blit(scaled_player, mini_player_pos)

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
        mtopleftidx = tuple((minimap_tiles[i] - 1)/2 - mazepos[i] for i in range(2))
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
    heart_size = config_ui["heart_size"]
    heart_img = imglib.load_image_from_file("images/sl/hearts/Full.png", after_scale=heart_size)
    halfheart_img = imglib.load_image_from_file("images/sl/hearts/Half.png", after_scale=heart_size)
    emptyheart_img = imglib.load_image_from_file("images/sl/hearts/Empty.png", after_scale=heart_size)
    # Invulnerable hearts (empty invulnerable heart is the same as the normal)
    heartinv_img = imglib.load_image_from_file("images/sl/hearts/FullInv.png", after_scale=heart_size)
    halfheartinv_img = imglib.load_image_from_file("images/sl/hearts/HalfInv.png", after_scale=heart_size)
    def __init__(self, game, player):
        super().__init__(game, player)
        self.last_max_health_points = self.player.max_health_points
        self.heart_surface = self.new_heart_surface()
        self.update_hearts()

    def update(self):
        pass

    def get_hp_half_round(self):
        check = self.player.health_points * 2
        return int(check) / 2 if check % 1 else self.player.health_points

    def new_heart_surface(self):
        hearts = self.player.max_health_points
        width = self.heart_size[0] * hearts + config_ui["hearts_gap"] * (hearts - 1)
        height = self.heart_size[1]
        # Don't ask why. Elsehow it clips the hearts.
        width += 4; height += 4
        return pygame.Surface((width, height))

    def update_hearts(self):
        if self.player.max_health_points != self.last_max_health_points:
            self.last_max_health_points = self.player.max_health_points
            self.heart_surface = self.new_heart_surface()
        invincible = self.player.invincible_hearts_render
        heart_img = self.heartinv_img if invincible else self.heart_img
        halfheart_img = self.halfheartinv_img if invincible else self.halfheart_img
        rhealth = self.get_hp_half_round()
        rect = pygame.Rect(config_ui["hearts_pos"], self.heart_size)
        gap = config_ui["hearts_gap"]
        drawn = 0
        self.heart_surface.fill(Color.Black)
        if rhealth > 0:
            for h in range(math.floor(rhealth)):
                self.heart_surface.blit(heart_img, rect); drawn += 1
                rect.x += self.heart_size[0] + gap
            if rhealth % 1 == 0.5:
                self.heart_surface.blit(halfheart_img, rect); drawn += 1
                rect.x += self.heart_size[0] + gap
            for h in range(self.player.max_health_points - drawn):
                self.heart_surface.blit(self.emptyheart_img, rect); drawn += 1
                rect.x += self.heart_size[0] + gap
        else:
            for h in range(self.player.max_health_points):
                self.heart_surface.blit(self.emptyheart_img, rect); drawn += 1
                rect.x += self.heart_size[0] + gap

    def draw(self, screen):
        screen.blit(self.heart_surface, config_ui["hearts_pos"])


class SelectedItemBoxWidget(AbstractUIWidget):
    box_pos = config_ui["selected_item_box_pos"]
    box_size = config_ui["selected_item_box_size"]
    icon_move = config_ui["selected_item_box_icon_move"]
    icon_pos = (box_pos[0] + icon_move[0], box_pos[1] + icon_move[1])
    icon_size = config_ui["selected_item_box_icon_size"]
    box_image = imglib.load_image_from_file("images/sl/ui/SelectedItemBox.png", after_scale=box_size)
    def __init__(self, game, player):
        super().__init__(game, player)
        self.last_selected = self.last_icon = None
        self.update()

    def update(self):
        if self.player.selected_item is not self.last_selected:
            if self.last_selected is not self.player.inventory.empty_slot:
                del imglib.scale_cache[(self.last_selected.icon, self.icon_size)]
            self.last_selected = self.player.selected_item
            if self.last_selected is not self.player.inventory.empty_slot:
                self.scaled_icon = imglib.scale(self.last_selected.icon, self.icon_size)

    def draw(self, screen):
        screen.blit(self.box_image, self.box_pos)
        if self.player.selected_item is not self.player.inventory.empty_slot:
            screen.blit(self.scaled_icon, self.icon_pos)
