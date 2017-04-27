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

reverse_directions = {"left": "right", "right": "left", 
                      "up": "down", "down": "up"}
directions_base = {"left": "left", "right": "right", 
                  "top": "up", "bottom": "down"}

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
        screen.blit(self.background, TOPLEFT)

        screen.blit(self.title_text, self.config["positions"]["title_text"])

        for key, value in self.buttons.items():
            pos = self.config["positions"]["buttons"][key]
            used = self.buttons[key][self.mouse_hovering_over[key]]
            screen.blit(used, pos)

        screen.blit(self.border, TOPLEFT)

    def start_game(self):
        gen = mazegen.MazeGenerator(*self.game.vars["mapsize"])
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
            if "screen" in game.vars:
                self.parent_surface = self.game.vars["screen"]
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
    config_ui = json.load(open("configs/playerui.json"))
    def __init__(self, game, *, level, entry_dir="any", player=None, run_interlude=False):
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
            self.handle_level_travel()

    def draw(self, screen, *, dlevel=True, dplayer=True, dui=True, dborder=True):
        if dlevel:      
            self.level.draw(screen, self.pos_fix)

        if dplayer:     
            self.player.draw(screen, self.pos_fix)
        elif not dplayer and dui:
            self.player.draw_ui(screen, self.pos_fix)

        if dborder:     
            screen.blit(self.border, TOPLEFT)


    def handle_level_travel(self):
        passage = self.player.near_passage
        direction = self.level.start_entries_rev[passage.index]
        mx, my = self.game.vars["player_mazepos"]
        if direction == "left":     mx -= 1
        elif direction == "right":  mx += 1
        elif direction == "top":    my -= 1
        elif direction == "bottom": my += 1
        newlevel = self.game.vars["map"][my][mx]
        print(self.game.vars["player_mazepos"], "-->", (mx, my), "dir:", direction)
        self.game.vars["player_mazepos"] = (mx, my)
        opposite_dir = levels.opposite_dirs[direction]

        self.game.pop_state()
        self.cleanup()
        new_state = DungeonState(self.game, level=newlevel(), entry_dir=opposite_dir, 
                                 player=self.player, run_interlude=True)
        ssize = self.game.vars["screen"].get_size()
        levelcrop = pygame.Rect(self.config["level_surface_position"], self.config["level_surface_size"])
        topbarcrop = pygame.Rect(self.config["topbar_position"], self.config["topbar_size"])
        surface1 = pygame.Surface(ssize)
        self.draw(surface1, dplayer=False, dborder=False)
        surface1 = surface1.subsurface(levelcrop)
        surface2 = pygame.Surface(ssize)
        new_state.draw(surface2, dplayer=False, dui=True, dborder=False)
        topbar = surface2.subsurface(topbarcrop)
        surface2 = surface2.subsurface(levelcrop)

        interlude_way = reverse_directions[directions_base[direction]]
        static_elems = [(self.config["topbar_position"], topbar)]
        interlude = InterludeState(self.game, first=surface1, second=surface2, way=interlude_way, 
                                   static_elems=static_elems, fix=self.config["level_surface_position"])
        self.game.push_state(new_state)
        self.game.push_state(interlude)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Interlude State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state draws the current surface and then moves
# to the next one, and thus requires 'first',
# 'second' and 'way' keyword arguments. 
# The 'way' argument is a string: either 
# "left", "right", "up" or "down".
# The 'speed' keyword argument is optional, default 4. 

class InterludeState(AbstractGameState):
    def __init__(self, game, *, first, second, way, speed=3, static_elems=[], fix=(0, 0)):
        super().__init__(game)

        self.first, self.second = first, second
        self.way, self.speed = way, speed
        self.static_elems = static_elems
        self.fix = fix

        assert self.way in ("left", "right", "up", "down")
        first_w, first_h = self.first.get_size()
        second_w, second_h = self.second.get_size()
        if self.way == "left" or self.way == "right":
            surface_size = (first_w + second_w,
                            max(first_h, second_h))
        else:
            surface_size = (max(first_w, second_w),
                            first_h + second_h)
        self.surface = pygame.Surface(surface_size)
        self.rect = self.surface.get_rect()

        if self.way == "left":
            self.rect.x = 0
            self.surface.blit(self.first, (0, 0))
            self.surface.blit(self.second, (first_w, 0))
            self.ticks_left = first_w // speed
        elif self.way == "right":
            self.rect.x = -self.second.get_width()
            self.surface.blit(self.second, (0, 0))
            self.surface.blit(self.first, (second_w, 0))
            self.ticks_left = second_w // speed
        elif self.way == "up":
            self.rect.y = 0
            self.surface.blit(self.first, (0, 0))
            self.surface.blit(self.second, (0, first_h))
            self.ticks_left = first_h // speed
        elif self.way == "down":
            self.rect.y = -self.second.get_height()
            self.surface.blit(self.second, (0, 0))
            self.surface.blit(self.first, (0, second_h))
            self.ticks_left = second_h // speed

    def cleanup(self):
        super().cleanup()

    def pause(self):
        super().pause()

    def resume(self):
        super().resume()

    def handle_events(self, events, pressed_keys, mouse_pos):
        pass

    def update(self):
        if self.way == "left":
            self.rect.x -= self.speed
        elif self.way == "right":
            self.rect.x += self.speed
        elif self.way == "up":
            self.rect.y -= self.speed
        elif self.way == "down":
            self.rect.y += self.speed
        self.ticks_left -= 1
        if self.ticks_left == 0:
            if self.way == "left":
                self.rect.x = -self.first.get_width()
            elif self.way == "right":
                self.rect.x = 0
            elif self.way == "up":
                self.rect.y = -self.first.get_height()
            elif self.way == "down":
                self.rect.y = 0
        if self.ticks_left == -1:
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        if self.fix == (0, 0):
            screen.blit(self.surface, self.rect)
        else:
            screen.blit(self.surface, (self.rect.x + self.fix[0], self.rect.y + self.fix[1]))
        for pos, surface in self.static_elems:
            screen.blit(surface, pos)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====


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

