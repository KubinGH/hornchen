import math
import pygame

import json_ext as json
from colors import Color
import imglib
from abc_uiwidget import AbstractUIWidget

print("Load player UI")

config_ui = json.loadf("configs/playerui.json")



class MinimapWidget(AbstractUIWidget):
    minimap_tile = config_ui["minimap_blocksize"]
    minimap_tile_t = (minimap_tile, minimap_tile)
    minimap_tiles = config_ui["minimap_tiles"]
    question_mark = imglib.load_image_from_file("images/sl/minimap/QuestionMarkM.png", after_scale=minimap_tile_t)
    tile_empty = imglib.load_image_from_file("images/dd/env/Bricks.png", after_scale=minimap_tile_t)
    tile_wall = imglib.load_image_from_file("images/dd/env/WallSmall.png", after_scale=minimap_tile_t)
    border_color = (0, 29, 109) 
    def __init__(self, game, player):
        super().__init__(game, player)
        full_minimap_size_px = (self.game.vars["mapsize"][0] * self.minimap_tile, 
                                self.game.vars["mapsize"][1] * self.minimap_tile)
        self.background = imglib.repeated_image_texture(self.question_mark, full_minimap_size_px)
        self.full_surface = pygame.Surface(full_minimap_size_px)
        self.surface = pygame.Surface(config_ui["minimap_size"])
        self.rect = self.surface.get_rect()
        self.border = imglib.color_border(config_ui["minimap_size"], self.border_color, 4, nowarn=True)
        self.tile_current = self.new_tile_current_surface()

    def update_full(self):
        self.full_surface.fill(Color.Black)
        self.full_surface.blit(self.background, (0, 0))
        mazepos = self.game.vars["player_mazepos"]
        for row, irow in enumerate(self.game.vars["maze"]):
            for col, bit in enumerate(irow):
                x, y = col * self.minimap_tile, row * self.minimap_tile
                rect = pygame.Rect((x, y), self.minimap_tile_t)
                if (col, row) == mazepos:
                    tile = self.tile_current
                elif self.player.map_reveal[row][col]:
                    tile = self.tile_wall if bit else self.tile_empty
                else:
                    continue
                self.full_surface.blit(tile, rect)

    def update_part(self):
        mazepos = self.game.vars["player_mazepos"]
        mtopleftidx = tuple((self.minimap_tiles[i] - 1)/2 - mazepos[i] for i in range(2))
        mtopleft = mtopleftidx[0] * self.minimap_tile, mtopleftidx[1] * self.minimap_tile
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

    def new_tile_current_surface(self):
        surface = self.tile_empty.copy()
        mini_player_size = (int(self.minimap_tile/1.2), int(self.minimap_tile/1.2))
        scaled_player = imglib.scale(self.player.surface, mini_player_size)
        s_rect = scaled_player.get_rect()
        mini_player_pos = (int((self.minimap_tile-s_rect.width)/2), int((self.minimap_tile-s_rect.height)/2))
        surface.blit(scaled_player, mini_player_pos)
        return surface

class HeartsWidget(AbstractUIWidget):
    heart_size = config_ui["heart_size"]
    hearts_pos = config_ui["hearts_pos"]
    hearts_gap = config_ui["hearts_gap"]
    heart_img = imglib.load_image_from_file("images/sl/hearts/Full.png", after_scale=heart_size)
    halfheart_img = imglib.load_image_from_file("images/sl/hearts/Half.png", after_scale=heart_size)
    emptyheart_img = imglib.load_image_from_file("images/sl/hearts/Empty.png", after_scale=heart_size)
    # Invulnerable hearts (empty invulnerable heart is the same as the normal)
    heartinv_img = imglib.load_image_from_file("images/sl/hearts/FullInv.png", after_scale=heart_size)
    halfheartinv_img = imglib.load_image_from_file("images/sl/hearts/HalfInv.png", after_scale=heart_size)
    def __init__(self, game, player):
        super().__init__(game, player)
        self.heart_draws = []
        self.top_heart = None
        self.update_hearts()

    def update(self):
        if self.player.last_health_points != self.player.health_points or \
          bool(self.player.last_invincibility_ticks) != bool(self.player.invincibility_ticks) or \
          math.ceil(self.player.max_health_points) != len(self.heart_draws):
           self.update_hearts()


    def get_hp_half_round(self):
        check = self.player.health_points * 2
        return int(check) / 2 if check % 1 else self.player.health_points

    def update_hearts(self):
        self.heart_draws.clear()
        self.top_heart = 0
        invincible = bool(self.player.invincibility_ticks)
        heart_img = self.heartinv_img if invincible else self.heart_img
        halfheart_img = self.halfheartinv_img if invincible else self.halfheart_img
        emptyheart_img = self.emptyheart_img
        rhealth = self.get_hp_half_round()
        rect = pygame.Rect(self.hearts_pos, self.heart_size)
        gap = self.hearts_gap
        drawn = 0
        if rhealth > 0:
            for h in range(math.floor(rhealth)):
                self.heart_draws.append((heart_img, rect.copy()))
                drawn += 1
                rect.x += self.heart_size[0] + gap
                self.top_heart = drawn - 1
            if rhealth % 1 == 0.5:
                self.heart_draws.append((halfheart_img, rect.copy()))
                drawn += 1
                rect.x += self.heart_size[0] + gap
                self.top_heart = drawn - 1
            for h in range(math.ceil(self.player.max_health_points) - drawn):
                self.heart_draws.append((emptyheart_img, rect.copy()))
                drawn += 1
                rect.x += self.heart_size[0] + gap
        else:
            for h in range(math.ceil(self.player.max_health_points)):
                self.heart_draws.append((emptyheart_img, rect.copy()))
                drawn += 1
                rect.x += self.heart_size[0] + gap
        if rect.x > 500 and self.hearts_gap > -self.heart_size[0]:
            self.hearts_gap -= 1
            self.update_hearts()

    def draw(self, screen):
        #screen.blit(self.heart_surface, config_ui["hearts_pos"])
        for i, pair in enumerate(self.heart_draws):
            if i == self.top_heart:
                continue
            img, rect = pair
            screen.blit(img, rect)
        top = self.heart_draws[self.top_heart]
        screen.blit(top[0], top[1])

class StarsWidget(AbstractUIWidget):
    mana_per_star = config_ui["mana_per_star"]
    star_main_color = config_ui["star_main_color"]
    star_size = config_ui["star_size"]
    stars_pos = config_ui["stars_pos"]
    stars_gap = config_ui["stars_gap"]
    star_img = imglib.load_image_from_file("images/sl/stars/Star.png", after_scale=star_size)
    main_r, main_g, main_b = star_main_color
    star_images = []
    _get_trans_color = lambda v, fr, m=255: v + (m - v) * fr
    for i in range(mana_per_star + 1):
        star_array = pygame.PixelArray(star_img.copy())
        _fr = 1 - (i / mana_per_star)
        if _fr > 0:
            repcolor = (_get_trans_color(main_r, _fr, 160), _get_trans_color(main_g, _fr, 160), _get_trans_color(main_b, _fr))
            star_array.replace(star_main_color, repcolor, 0.4)
        star_images.append(star_array.surface)
        del star_array
    def __init__(self, game, player):
        super().__init__(game, player)
        self.star_draws = []
        self.top_star = None
        self.update_stars()

    def update(self):
        if self.player.last_mana_points != self.player.mana_points or \
           math.ceil(self.player.max_mana_points / self.mana_per_star) != len(self.star_draws):
            self.update_stars()

    def update_stars(self):
        self.star_draws.clear()
        self.top_star = 0
        rect = pygame.Rect(self.stars_pos, self.star_size)
        count = math.ceil(self.player.max_mana_points / self.mana_per_star)
        drawn = 0
        for i in range(self.player.mana_points // self.mana_per_star):
            self.star_draws.append((self.star_images[self.mana_per_star], rect.copy()))
            rect.x += self.star_size[0] + self.stars_gap
            drawn += 1
            self.top_star = drawn - 1
        if drawn == count:
            return
        self.star_draws.append((self.star_images[self.player.mana_points % 20], rect.copy()))
        rect.x += self.star_size[0] + self.stars_gap
        drawn += 1
        self.top_star = drawn - 1
        while drawn != count:
            self.star_draws.append((self.star_images[0], rect.copy()))
            rect.x += self.star_size[0] + self.stars_gap
            drawn += 1
        if rect.x > 500 and self.stars_gap > -self.star_size[0]:
            self.stars_gap -= 1
            self.update_stars()

    def draw(self, screen):
        for i, pair in enumerate(self.star_draws):
            if i == self.top_star:
                continue
            img, rect = pair
            screen.blit(img, rect)
        top = self.star_draws[self.top_star]
        screen.blit(top[0], top[1])

class SelectedItemBoxWidget(AbstractUIWidget):
    box_pos = config_ui["selected_item_box_pos"]
    box_size = config_ui["selected_item_box_size"]
    icon_move = config_ui["selected_item_box_icon_move"]
    icon_pos = (box_pos[0] + icon_move[0], box_pos[1] + icon_move[1])
    icon_size = config_ui["selected_item_box_icon_size"]
    box_image = imglib.load_image_from_file("images/sl/ui/SelectedItemBox.png", after_scale=box_size)
    def __init__(self, game, player):
        super().__init__(game, player)
        self.display_icon = self.last_selected = self.last_icon = None
        self.update()

    def update(self):
        select = self.player.selected_item
        if select is not self.last_selected:
            self.last_selected = select
            if select is not self.player.inventory.empty_slot:
                self.display_icon = imglib.scale(select.icon, self.icon_size, docache=False)
            else:
                self.display_icon = None

    def draw(self, screen):
        screen.blit(self.box_image, self.box_pos)
        if self.display_icon is not None:
            screen.blit(self.display_icon, self.icon_pos)

class SelectedSpellBoxWidget(AbstractUIWidget):
    box_pos = config_ui["selected_spell_box_pos"]
    box_size = config_ui["selected_spell_box_size"]
    icon_move = config_ui["selected_spell_box_icon_move"]
    icon_pos = (box_pos[0] + icon_move[0], box_pos[1] + icon_move[1])
    icon_size = config_ui["selected_spell_box_icon_size"]
    box_image = imglib.load_image_from_file("images/sl/ui/SelectedSpellBox.png", after_scale=box_size)
    def __init__(self, game, player):
        super().__init__(game, player)
        self.display_icon = self.last_selected = self.last_icon = None
        self.update()

    def update(self):
        select = self.player.selected_spell
        if self.player.selected_spell is not self.last_selected:
            self.last_selected = select
            if select is not None:
                self.display_icon = imglib.scale(select.icon, self.icon_size, docache=False)
            else:
                self.display_icon = None

    def draw(self, screen):
        screen.blit(self.box_image, self.box_pos)
        if self.display_icon is not None:
            screen.blit(self.display_icon, self.icon_pos)
