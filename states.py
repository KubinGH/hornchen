import random
import warnings

import pygame

import json_ext as json
import fontutils
import imglib
from abc_state import AbstractGameState
import levels
from colors import Color
import mapgen
from libraries import mazegen

print("Load states")

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
    lazy_state = True
    config = json.load(open("configs/mainmenu.json", "r"))
    def __init__(self, game):
        super().__init__(game)

        self.logo_sword = imglib.load_image_from_file("images/tr/LogoSword.png")
        self.bg_tile = imglib.load_image_from_file("images/dd/env/Bricks.png", after_scale=(40, 40))
        self.background = imglib.repeated_image_texture(self.bg_tile, self.game.vars["screen_size"])
        self.border_drawer = imglib.ColorBorderDrawer(self.game.vars["screen_size"], (0, 29, 109), 3)
        
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

        self.border_drawer.draw(screen, TOPLEFT)

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
    lazy_state = True
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

        self.bg_tile = imglib.load_image_from_file("images/dd/env/BricksSmall.png", after_scale=(20, 20))
        self.border_tile = imglib.load_image_from_file("images/dd/env/WallDim.png", after_scale=(20, 20))
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
            print("Cache cleared by PauseState")
            self.game.vars["level_caches"] = {}
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

        self.border_drawer = imglib.ColorBorderDrawer(self.game.vars["screen_size"], 
                                                      self.config["border_color"], 
                                                      self.config["border_thickness"])

        self.player = player
        self.player.level = self.level
        if self.level.start_entries[entry_dir] is not None:
            entry_dir_pos = self.level.start_entries[entry_dir]
        else:
            if self.level.start_entries["any"] is not None:
                entry_dir_pos = self.level.start_entries["any"]
            else:
                warnings.warn("DungeonState: Unspecified entry point from " + \
                              "direction {} at level from {}".format(entry_dir, self.level.source))
                entry_dir_pos = (0, 0)

        self.player.rect.center = self.level.layout[entry_dir_pos[1]][entry_dir_pos[0]].rect.center

        self.player.on_new_level()
        self.level.update()

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
            self.border_drawer.draw(screen, TOPLEFT)


    def handle_level_travel(self):
        # Through which door is the player going
        passage = self.player.near_passage 
        # Direction of player movement on the map
        direction = self.level.start_entries_rev[passage.index] 
        # Compute the next position
        next_x, next_y = last_x, last_y = self.game.vars["player_mazepos"]
        if direction == "left":     next_x -= 1
        elif direction == "right":  next_x += 1
        elif direction == "top":    next_y -= 1
        elif direction == "bottom": next_y += 1
        print((last_x, last_y), "-->", (next_x, next_y), "dir:", direction)
        opposite_dir = levels.opposite_dirs[direction]
        self.handle_next_level(last_x, last_y, next_x, next_y, direction, opposite_dir, True)

    def handle_next_level(self, last_x, last_y, next_x, next_y, door_dir, entry_dir, use_interlude=True):
        last_x = self.game.vars["player_mazepos"][0] if last_x is None else last_x
        last_y = self.game.vars["player_mazepos"][1] if last_y is None else last_y
        self.game.vars["level_caches"][(last_x, last_y)] = self.level.create_cache()
        self.game.pop_state()
        self.cleanup()
        newlevel = self.game.vars["map"][next_y][next_x]
        self.game.vars["player_mazepos"] = (next_x, next_y)
        if newlevel is None:
            newlevel = levels.EmptyLevel
        if (next_x, next_y) in self.game.vars["level_caches"]:
            newlevelobj = newlevel.load_from_cache(self.game.vars["level_caches"][(next_x, next_y)])
        else:
            newlevelobj = newlevel()
        new_state = DungeonState(self.game, level=newlevelobj, entry_dir=entry_dir, 
                                 player=self.player, run_interlude=True)
        if use_interlude:
            # Draw a frame of the game in each state (those are on different levels),
            # then save some of the UI elements (border, topbar) - static_elems,
            # and then create and InterludeState.
            ssize = self.game.vars["screen"].get_size()
            # Crops used
            levelcrop = pygame.Rect(self.config["level_surface_position"], self.config["level_surface_size"])
            topbarcrop = pygame.Rect(self.config["topbar_position"], self.config["topbar_size"])
            # Current (before)
            surface1 = pygame.Surface(ssize)
            self.draw(surface1, dplayer=False, dborder=False)
            surface1 = surface1.subsurface(levelcrop)
            # Next (after)
            surface2 = pygame.Surface(ssize)
            new_state.draw(surface2, dplayer=False, dui=True, dborder=False)
            topbar = surface2.subsurface(topbarcrop) # The updated topbar, e.g. minimap
            surface2 = surface2.subsurface(levelcrop)

            interlude_way = reverse_directions[directions_base[door_dir]]
            static_elems = [(self.config["topbar_position"], topbar)]
            drawers = [(self.border_drawer, TOPLEFT)]
            interlude = InterludeState(self.game, first=surface1, second=surface2, way=interlude_way, 
                                       static_elems=static_elems, drawers=drawers, fix=self.config["level_surface_position"])

        self.game.push_state(new_state)
        if use_interlude:
            self.game.push_state(interlude)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Interlude State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state draws the current surface and then moves
# to the next one, and thus requires 'first',
# 'second' and 'way' keyword arguments. 
# The 'way' argument is a string: either 
# "left", "right", "up" or "down".

class InterludeState(AbstractGameState):
    def __init__(self, game, *, first, second, way, speed=3, static_elems=[], drawers=[], fix=(0, 0)):
        super().__init__(game)

        self.first, self.second = first, second
        self.way, self.speed = way, speed
        self.static_elems = static_elems
        self.drawers = drawers
        self.fix = fix

        # Here the program merges the two surfaces and then
        # handles the way it will scroll.
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
        for drawer, pos in self.drawers:
            drawer.draw(screen, pos)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
