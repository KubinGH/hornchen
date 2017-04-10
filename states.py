import random
import json_ext as json

import pygame

import fontutils
import imglib
from abc_state import AbstractGameState
import levels
from colors import Color
import mapgen

from libraries import mazegen

TOPLEFT = (0, 0)

MAZESIZE = (10, 10)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Test State       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class TestState(AbstractGameState):
    def __init__(self, game):
        super().__init__(game)

        self.rect = pygame.rect.Rect(0, 0, 40, 40)
        self.last_rect = None
        self.step = 4
        self.changed = False
        self.force_refresh = True

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.step = 4 if self.step != 4 else 12
                elif event.key == pygame.K_e:
                    self.game.pop_state()
                    self.cleanup()
                elif event.key == pygame.K_ESCAPE:
                    self.game.push_state(PauseState(self.game))
        self.last_rect = self.rect.copy()
        self.changed = False
        if pressed_keys[pygame.K_LEFT]:
            if self.rect.x - self.step >= 0:
                self.rect.x -= self.step
                self.changed = True
            else:
                self.rect.x = 0
        if pressed_keys[pygame.K_RIGHT]:
            if self.rect.x + self.rect.width + self.step <= self.game.vars["screen_size"][0]:
                self.rect.x += self.step
                self.changed = True
            else:
                self.rect.x = self.game.vars["screen_size"][0] - self.rect.width
        if pressed_keys[pygame.K_UP]:
            if self.rect.y - self.step >= 0:
                self.rect.y -= self.step
                self.changed = True
            else:
                self.rect.y = 0
        if pressed_keys[pygame.K_DOWN]:
            if self.rect.y + self.rect.height + self.step <= self.game.vars["screen_size"][1]:
                self.rect.y += self.step
                self.changed = True
            else:
                self.rect.y = self.game.vars["screen_size"][1] - self.rect.height

    def update(self):
        pass

    def draw(self, screen):
        if self.changed or self.force_refresh:
            self.changed = False
            pygame.draw.rect(screen, Color.Black, self.last_rect)
            pygame.draw.rect(screen, Color.Red,  self.rect)
            if self.force_refresh:
                return None
            else:
                return [self.last_rect, self.rect]
        else:
            return []

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Main Menu State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class MainMenuState(AbstractGameState):
    config = json.load(open("configs/mainmenu.json", "r"))
    def __init__(self, game):
        super().__init__(game)

        self.logo_sword = imglib.load_image_from_file("images/tr/LogoSword.png")
        self.bg_tile = imglib.load_image_from_file("images/dd/env/Bricks.png")
        self.bg_tile = imglib.scale2x(self.bg_tile)
        self.background = imglib.repeated_image_texture(self.bg_tile, self.game.vars["screen_size"])
        self.border = imglib.color_border(self.game.vars["screen_size"], (0, 29, 109), 3)
        
        self.font = fontutils.get_font("fonts/OldLondon.ttf", self.config["fonts"]["sizes"]["font"])
        self.font_large = fontutils.get_font("fonts/OldLondon.ttf", self.config["fonts"]["sizes"]["font_large"])
        self.title_text = fontutils.get_text_render(self.font_large, "Hornchen", True, Color.White)

        btext_pair = lambda text: [fontutils.get_text_render(self.font, text, True, Color.White), 
                                   fontutils.get_text_render(self.font, text, True, Color.Yellow)]
        self.buttons = {
            "start": btext_pair("Start"),
            "settings": btext_pair("Settings")
        }
        self.mouse_hovering_over = {key: False for key in self.buttons}
        self.pressed_buttons = {key: False for key in self.buttons}
        self.button_rects = {key: pygame.Rect(self.config["positions"]["buttons"][key], 
                                              self.buttons[key][0].get_size()) 
                             for key in self.buttons}

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):
        self.mouse_hovering_over = {key: False for key in self.buttons}
        self.pressed_buttons = {key: False for key in self.buttons}

        for key, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                self.mouse_hovering_over[key] = True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for key in self.buttons:
                    if self.mouse_hovering_over[key]:
                        print("MainMenu::Pressed", key)
                        self.pressed_buttons[key] = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.pressed_buttons["start"] = True

    def update(self):
        if self.pressed_buttons["start"]:
            self.start_game()

    def draw(self, screen):
        screen.fill(Color.Black)

        screen.blit(self.background, TOPLEFT)

        screen.blit(self.title_text, self.config["positions"]["title_text"])

        for key, value in self.buttons.items():
            pos = self.config["positions"]["buttons"][key]
            used = self.buttons[key][self.mouse_hovering_over[key]]
            screen.blit(used, pos)

        screen.blit(self.border, TOPLEFT)

    def start_game(self):
        gen = mazegen.MazeGenerator(*MAZESIZE)
        gen.create2()
        self.game.vars["maze"] = gen.data
        self.game.vars["player_mazepos"] = gen.start_pos
        self.game.vars["map"] = [[None for _ in range(gen.width)] for _ in range(gen.height)]
        mapgen.generate_map(self.game.vars["map"], gen)
        start_level = self.game.vars["map"][gen.start_pos[1]][gen.start_pos[0]]
        self.game.push_state(DungeonState(self.game, level=start_level(), player=self.game.player))

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====       Pause State       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state requires the last drawing surface, and the
# creator of this state should provide a 'parent_surface'
# keyword argument.

class PauseState(AbstractGameState):
    config = json.load(open("configs/pause.json", "r"))   
    pause_window_size = config["sizes"]["pause_window"]
    pause_window_pos = config["positions"]["pause_window"]
    pause_text_pos = config["positions"]["pause_text"]
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)

        if parent_surface is None:
            if "draw_surface" in game.vars:
                self.parent_surface = self.game.vars["draw_surface"]
            else:
                self.parent_surface = pygame.Surface(self.game.vars["screen_size"])
                self.parent_surface.fill(Color.Black)
        else:
            self.parent_surface = parent_surface
        self.parent_surface = self.parent_surface.copy()

        self.back_dimmer = pygame.Surface(self.game.vars["screen_size"])
        self.back_dimmer.fill(Color.Black)
        self.back_dimmer.set_alpha(125)
        self.parent_surface.blit(self.back_dimmer, TOPLEFT)

        self.bg_tile = imglib.load_image_from_file("images/dd/env/BricksSmall.png")
        self.border_tile = imglib.load_image_from_file("images/dd/env/WallDim.png")
        self.pause_background = imglib.repeated_image_texture(self.bg_tile, self.pause_window_size)
        self.parent_surface.blit(self.pause_background, self.pause_window_pos)
        self.pause_background_border = imglib.image_border(self.pause_window_size, self.border_tile)
        self.parent_surface.blit(self.pause_background_border, self.pause_window_pos)

        self.font = fontutils.get_font("fonts/OldLondon.ttf", self.config["font_size"])
        self.pause_text = fontutils.get_text_render(self.font, "Paused", True, Color.White)
        self.parent_surface.blit(self.pause_text, self.pause_text_pos)

        btext_pair = lambda text: [fontutils.get_text_render(self.font, text, True, Color.White), 
                                   fontutils.get_text_render(self.font, text, True, Color.Yellow)]
        self.buttons = {
            "return": btext_pair("Return"),
            "exit":   btext_pair(" Exit ")
        }
        self.mouse_hovering_over = {key: False for key in self.buttons}
        self.pressed_buttons = {key: False for key in self.buttons}
        self.button_rects = {key: pygame.Rect(self.config["positions"]["buttons"][key], 
                                              self.buttons[key][0].get_size()) 
                             for key in self.buttons}

        self.leaving = False

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):        
        self.mouse_hovering_over = {key: False for key in self.buttons}
        self.pressed_buttons = {key: False for key in self.buttons}

        for key, rect in self.button_rects.items():
            if rect.collidepoint(mouse_pos):
                self.mouse_hovering_over[key] = True

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.leaving = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for key in self.buttons:
                    if self.mouse_hovering_over[key]:
                        self.pressed_buttons[key] = True

    def update(self):
        if self.pressed_buttons["return"]:
            self.leaving = True

        if self.pressed_buttons["exit"]:
            self.game.pop_state()
            self.cleanup()
            while not isinstance(self.game.top_state, MainMenuState):
                nxt = self.game.pop_state()
                nxt.cleanup()
            return

        if self.leaving:    
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        screen.blit(self.parent_surface, TOPLEFT)
        for key, value in self.buttons.items():
            pos = self.config["positions"]["buttons"][key]
            used = self.buttons[key][self.mouse_hovering_over[key]]
            screen.blit(used, pos)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====      Dungeon State      ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state requires the level that will be run,
# thus it requires the 'level' and 'entry_dir' keyword arguments.
# The 'player' keyword argument should also be provided, or a new
# player will be created.

class DungeonState(AbstractGameState):
    config = json.load(open("configs/dungeon.json", "r"))
    tile_size = config["tile_size"]
    pos_fix = config["level_surface_position"]
    def __init__(self, game, *, level, entry_dir="any", player=None):
        super().__init__(game)

        self.level = level
        self.level.parent = self

        self.border = imglib.color_border(self.game.vars["screen_size"], (0, 29, 109), 3)

        self.player = player
        self.player.current_level = self.level
        assert self.level.start_entries[entry_dir] is not None, "Unspecified entry point from direction {}".format(entry_dir)
        self.player.rect.x = self.level.start_entries[entry_dir][0] * self.tile_size
        self.player.rect.y = self.level.start_entries[entry_dir][1] * self.tile_size

        self.player.on_new_level()

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.push_state(PauseState(self.game))
        self.level.handle_events(events, pressed_keys, mouse_pos)
        self.player.handle_events(events, pressed_keys, mouse_pos)

    def update(self):
        self.level.update()
        self.player.update()
        if self.player.going_through_door:
            self.player.going_through_door = False
            passage = self.player.near_passage
            direction = self.level.start_entries_rev[passage.index]
            mx, my = self.game.vars["player_mazepos"]
            if direction == "left":     mx -= 1
            elif direction == "right":  mx += 1
            elif direction == "top":    my -= 1
            elif direction == "bottom": my += 1
            newlevel = self.game.vars["map"][my][mx]
            print(self.game.vars["player_mazepos"], "-->", (mx, my))
            self.game.vars["player_mazepos"] = (mx, my)
            opposite_dir = levels.opposite_dirs[direction]
            self.game.pop_state()
            self.cleanup()
            self.game.push_state(DungeonState(self.game, level=newlevel(), entry_dir=opposite_dir, player=self.player))


    def draw(self, screen):
        screen.fill(Color.Black)
        self.level.draw(screen, self.pos_fix)
        self.player.draw(screen, self.pos_fix)
        screen.blit(self.border, TOPLEFT)


class _FakeGame:
    vars = {"screen_size": (1024, 768)}
_fake_game_inst = _FakeGame()
_fake_surface_inst = pygame.Surface((1024, 768))

if __name__ == "__main__":
    pygame.init()
    s1 = TestState(_fake_game_inst)
    s2 = MainMenuState(_fake_game_inst)
    s3 = PauseState(_fake_game_inst, parent_surface=_fake_surface_inst)
    #s4 = DungeonState(_fake_game_inst, level=levels.start_level)

