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
import easing
import mazegen

print("Load states")

TOPLEFT = (0, 0)

reverse_directions = {"left": "right", "right": "left", 
                      "up": "down", "down": "up"}
directions_base = {"left": "left", "right": "right", 
                  "top": "up", "bottom": "down"}

config_ui = json.loadf("configs/playerui.json")
screen_size = config_ui["screen_size"]
menu_bg_tile = imglib.load_image_from_file("images/dd/env/Bricks.png", after_scale=(40, 40))
menu_background = imglib.repeated_image_texture(menu_bg_tile, screen_size)
menu_border_drawer = imglib.ColorBorderDrawer(screen_size, (0, 29, 109), 3)
menu_font = fontutils.get_font("fonts/OldLondon.ttf", 50)
menu_font_large = fontutils.get_font("fonts/OldLondon.ttf", 90)


class UIButton:
    def __init__(self, name, text, font, pos, colors=(Color.White, Color.Yellow)):
        self.name = name
        self.text, self.font = text, font
        self.pos, self.colors = pos, colors
        self.text_renders = [fontutils.get_text_render(self.font, text, True, color) for color in self.colors]
        self.rect = pygame.Rect(self.pos, self.text_renders[0].get_size())
        self.hovered_over = False
        self.pressed = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        self.hovered_over = self.rect.collidepoint(mouse_pos)
        self.pressed = self.hovered_over and any(event.type == pygame.MOUSEBUTTONDOWN for event in events)

    def update(self):
        pass

    def draw(self, screen):
        screen.blit(self.text_renders[self.hovered_over], self.rect)

class UISlider:
    def __init__(self, rects, length=70, fix=10, ease=easing.ease_in_out_cubic, ins=True):
        self.rects, self.length, self.fix, self.ease = rects, length, fix, ease
        self.tick = 0
        self.done = False
        self.side = min(-rect.width for rect in self.rects)
        if ins:
            self.args = [(self.side, -self.side + rect.x, self.length) for rect in self.rects]
        else:
            self.args = [(rect.x, self.side - rect.x, self.length) for rect in self.rects]
        for rect, args in zip(self.rects, self.args):
            rect.x = args[0]

    def update(self):
        for rect, args in zip(self.rects, self.args):
            rect.x = self.ease(self.tick, *args)
        self.tick += 1
        if self.tick > self.length:
            self.done = True

def get_parent_surface(game):
    if "screen" in game.vars:
        parent_surface = game.vars["screen"].copy()
    else:
        parent_surface = pygame.Surface(game.vars["screen_size"])
        parent_surface.fill(Color.Black)
    return parent_surface

def current_as_dimmed_bg(game, *, parent_surface=None, dimcolor=Color.Black, dim=125):
    if parent_surface is None:
        parent_surface = get_parent_surface(game)

    back_dimmer = pygame.Surface(game.vars["screen_size"])
    back_dimmer.fill(dimcolor)
    back_dimmer.set_alpha(dim)
    parent_surface.blit(back_dimmer, TOPLEFT)

    return parent_surface

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Main Menu State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class MainMenuState(AbstractGameState):
    lazy_state = True
    use_mouse = True
    config = json.loadf("configs/mainmenu.json")
    fade_length = 50
    def __init__(self, game, *, fade_in=False, slide_in=True, slide_out=True):
        super().__init__(game)
        self.fade_tick = 0
        self.fade_in = fade_in
        self.slide_in, self.slide_out = slide_in, slide_out
        self.sliding_in = self.sliding_out = False
        self.in_slider = self.out_slider = self.after_slide_out =  None

        self.background = menu_background.copy()
        
        self.title_text = fontutils.get_text_render(menu_font_large, "Hornchen", True, Color.White)
        self.title_text_rect = pygame.Rect(self.config["positions"]["title_text"], self.title_text.get_size())

        self.button_list = [
            UIButton("start", "Start", menu_font, self.config["positions"]["buttons"]["start"]),
            UIButton("settings", "Settings", menu_font, self.config["positions"]["buttons"]["settings"]),
            UIButton("exit", "Exit", menu_font, self.config["positions"]["buttons"]["exit"])
        ]
        self.buttons = {button.name: button for button in self.button_list}

        if self.fade_in:
            self.background.set_alpha(255)
        elif self.slide_in:
            self.set_slide_in()

    def resume(self):
        super().resume()
        self.title_text_rect.topleft = self.config["positions"]["title_text"]
        for button in self.button_list:
            button.rect.topleft = button.pos
        if self.slide_in:
            self.set_slide_in()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for button in self.button_list:
            button.handle_events(events, pressed_keys, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    if self.fade_in:
                        self.fade_tick = self.fade_length
                    elif self.sliding_in:
                        self.in_slider.tick = self.in_slider.length
                    elif self.sliding_out:
                        self.out_slider.tick = self.out_slider.length

    def update(self):
        if self.fade_in:
            alpha = (self.fade_tick / self.fade_length) * 255
            self.background.set_alpha(alpha)
            self.fade_tick += 1
            if self.fade_tick > self.fade_length:
                self.fade_in = False
                self.background = menu_background
                if self.slide_in:
                    self.set_slide_in()
        elif self.sliding_in:
            self.in_slider.update()
            if self.in_slider.done:
                self.sliding_in = False
                self.in_slider = None
        elif self.sliding_out:
            self.out_slider.update()
            if self.out_slider.done:
                self.sliding_out = False
                self.out_slider = None
                self.after_slide_out()
        if self.buttons["start"].pressed:
            self.start_game()
        elif self.buttons["settings"].pressed:
            if self.slide_out:
                self.set_slide_out()
                state = SettingsState(self.game, slide_in=True, slide_out=True)
                self.after_slide_out = lambda: self.game.push_state(state)
        elif self.buttons["exit"].pressed:
            print("Exit from Main Menu")
            self.game.vars["app"].running = False

    def draw(self, screen):
        if self.fade_in:
            screen.fill(Color.Black)
            screen.blit(self.background, TOPLEFT)
            menu_border_drawer.draw(screen, TOPLEFT)
            return
        screen.blit(self.background, TOPLEFT)
        screen.blit(self.title_text, self.title_text_rect)
        for button in self.button_list:
            button.draw(screen)
        menu_border_drawer.draw(screen, TOPLEFT)

    def start_game(self):
        self.game.reset_game()
        start_level = self.game.new_game()
        dungeon_state = DungeonState(self.game, level=start_level(), player=self.game.player)
        surface = pygame.Surface(self.game.vars["screen_size"])
        dungeon_state.draw(surface)
        self.game.push_state(dungeon_state)
        self.game.push_state(FadeInterludeState(self.game, first=get_parent_surface(self.game), second=surface))

    def set_slide_in(self):
        self.sliding_in = True
        rects = [self.title_text_rect] + [b.rect for b in self.button_list]
        self.in_slider = UISlider(rects)

    def set_slide_out(self):
        self.sliding_out = True
        rects = [self.title_text_rect] + [b.rect for b in self.button_list]
        self.out_slider = UISlider(rects, ins=False)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Settings State      ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class SettingsState(AbstractGameState):
    lazy_state = True
    use_mouse = True
    config = json.loadf("configs/settingsmenu.json")
    def __init__(self, game, *, slide_in=False, slide_out=False):
        super().__init__(game)
        self.slide_in, self.slide_out = slide_in, slide_out
        self.sliding_in = self.sliding_out = False
        self.in_slider = self.out_slider = self.after_slide_out = None

        self.settings_text = fontutils.get_text_render(menu_font_large, "Settings", True, Color.White)
        self.settings_text_rect = pygame.Rect(self.config["positions"]["settings_text"], self.settings_text.get_size())

        self.no_yes_text = [fontutils.get_text_render(menu_font, t, True, Color.White) for t in ("No", "Yes")]
        self.no_yes_text_pos = [self.config["positions"]["no_or_yes_right_side"] - self.no_yes_text[b].get_width() for b in range(2)]
        self.button_list = [
            UIButton("use_mouse", "Use Mouse", menu_font, self.config["positions"]["buttons"]["use_mouse"]),
            UIButton("back", "Back", menu_font, self.config["positions"]["buttons"]["back"])
        ]
        self.buttons = {button.name: button for button in self.button_list}

        use_mouse = self.game.vars["forced_mouse"]
        self.use_mouse_status_rect = pygame.Rect((self.no_yes_text_pos[use_mouse], self.buttons["use_mouse"].rect.y), self.no_yes_text[use_mouse].get_size())

        if self.slide_in:
            self.set_slide_in()

    def resume(self):
        super().resume()
        self.settings_text_rect.topleft = self.config["positions"]["settings_text"]
        for button in self.button_list:
            button.rect.topleft = button.pos
        if self.slide_in:
            self.set_slide_in()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for button in self.button_list:
            button.handle_events(events, pressed_keys, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if self.sliding_in:
                        self.in_slider.tick = self.in_slider.length
                    elif self.sliding_out:
                        self.out_slider.tick = self.out_slider.length

    def update(self):
        pygame.mouse.set_visible(True)
        if self.sliding_in:
            self.in_slider.update()
            if self.in_slider.done:
                self.sliding_in = False
                self.in_slider = None
        elif self.sliding_out:
            self.out_slider.update()
            if self.out_slider.done:
                self.sliding_out = False
                self.out_slider = None
                self.after_slide_out()

        if self.buttons["use_mouse"].pressed:
            self.game.vars["forced_mouse"] = not self.game.vars["forced_mouse"]
            use_mouse = self.game.vars["forced_mouse"]
            self.use_mouse_status_rect = pygame.Rect((self.no_yes_text_pos[use_mouse], self.buttons["use_mouse"].rect.y), self.no_yes_text[use_mouse].get_size())
        elif self.buttons["back"].pressed:
            if self.slide_out:
                self.set_slide_out()
                self.after_slide_out = lambda: self.game.pop_state()

    def draw(self, screen):
        screen.blit(menu_background, TOPLEFT)
        screen.blit(self.settings_text, self.settings_text_rect)
        for button in self.button_list:
            button.draw(screen)
            if button.name == "use_mouse":
                b = self.game.vars["forced_mouse"]
                screen.blit(self.no_yes_text[b], self.use_mouse_status_rect)
        menu_border_drawer.draw(screen, TOPLEFT)

    def set_slide_in(self):
        self.sliding_in = True
        rects = [self.settings_text_rect, self.use_mouse_status_rect] + [b.rect for b in self.button_list]
        self.in_slider = UISlider(rects)

    def set_slide_out(self):
        self.sliding_out = True
        rects = [self.settings_text_rect, self.use_mouse_status_rect] + [b.rect for b in self.button_list]
        self.out_slider = UISlider(rects, ins=False)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====       Pause State       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state requires the last drawing surface, and the
# creator of this state should provide a 'parent_surface'
# keyword argument.

class PauseState(AbstractGameState):
    lazy_state = True
    use_mouse = True
    config = json.loadf("configs/pause.json")   
    pause_window_size = config["sizes"]["pause_window"]
    pause_window_pos = config["positions"]["pause_window"]
    pause_text_pos = config["positions"]["pause_text"]
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)

        self.background = current_as_dimmed_bg(game, parent_surface=parent_surface, dim=125)

        self.bg_tile = imglib.load_image_from_file("images/dd/env/BricksSmall.png", after_scale=(20, 20))
        self.border_tile = imglib.load_image_from_file("images/dd/env/WallDim.png", after_scale=(20, 20))
        self.pause_background = imglib.repeated_image_texture(self.bg_tile, self.pause_window_size)
        self.background.blit(self.pause_background, self.pause_window_pos)
        self.pause_background_border = imglib.image_border(self.pause_window_size, self.border_tile)
        self.background.blit(self.pause_background_border, self.pause_window_pos)

        self.font = fontutils.get_font("fonts/OldLondon.ttf", self.config["font_size"])
        self.pause_text = fontutils.get_text_render(self.font, "Paused", True, Color.White)
        self.background.blit(self.pause_text, self.pause_text_pos)

        self.button_list = [
            UIButton("return", "Return", self.font, self.config["positions"]["buttons"]["return"]),
            UIButton("exit", "Exit", self.font, self.config["positions"]["buttons"]["exit"])
        ]
        self.buttons = {button.name: button for button in self.button_list}

        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):        
        for button in self.button_list:
            button.handle_events(events, pressed_keys, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.leaving = True

    def update(self):
        for button in self.button_list:
            button.update()

        if self.buttons["return"].pressed:
            self.leaving = True

        if self.buttons["exit"].pressed:
            self.game.pop_state()
            self.cleanup()
            while not isinstance(self.game.top_state, MainMenuState):
                nxt = self.game.pop_state()
                nxt.cleanup()
            print("Level caches cleared by PauseState")
            self.game.vars["level_caches"] = {}
            return

        if self.leaving:    
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        screen.blit(self.background, TOPLEFT)
        for button in self.button_list:
            button.draw(screen)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====      Dungeon State      ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state requires the level that will be run,
# thus it requires the 'level' and 'entry_dir' keyword arguments.
# The 'player' keyword argument should also be provided, or a new
# player will be created.

class DungeonState(AbstractGameState):
    config = json.loadf("configs/dungeon.json")
    tile_size = config["tile_size"]
    pos_fix = config["level_surface_position"]
    config_ui = json.loadf("configs/playerui.json")
    def __init__(self, game, *, level, entry_dir="any", player=None):
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

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            pass
        self.handle_state_creation_events(events, pressed_keys, mouse_pos)
        self.level.handle_events(events, pressed_keys, mouse_pos)
        self.player.handle_events(events, pressed_keys, mouse_pos)

    def handle_state_creation_events(self, events, pressed_keys, mouse_pos):
        gets = self.get_as_parent_surface
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game.push_state(PauseState(self.game, parent_surface=gets()))
                elif event.key == pygame.K_i:
                    self.game.push_state(PlayerInventoryState(self.game, parent_surface=gets()))
                elif event.key == pygame.K_m:
                    self.game.push_state(MinimapViewState(self.game, parent_surface=gets()))     

    def update(self):
        self.level.update()
        self.player.update()
        if self.player.health_points <= 0:
            self.game.pop_state()
            self.game.push_state(DeathScreenState(self.game, parent_surface=self.get_as_parent_surface()))
            return
        if self.player.going_through_door:
            self.player.going_through_door = False
            self.handle_level_travel()

    def draw(self, screen, *, dlevel=True, dplayer=True, dui=True, dborder=True):
        if dlevel:      
            self.level.draw(screen, self.pos_fix)
        if dplayer:     
            self.player.draw(screen, self.pos_fix)
        if dui:
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

    def handle_next_level(self, last_x, last_y, next_x, next_y, door_dir, entry_dir, use_interlude=True, use_time_pass=True):
        last_x = self.game.vars["player_mazepos"][0] if last_x is None else last_x
        last_y = self.game.vars["player_mazepos"][1] if last_y is None else last_y
        self.game.vars["level_caches"][(last_x, last_y)] = self.level.create_cache()
        self.game.pop_state()
        self.cleanup()
        newlevelcls = self.game.vars["map"][next_y][next_x]
        self.game.vars["player_mazepos"] = (next_x, next_y)
        if newlevelcls is None:
            newlevelcls = levels.EmptyLevel
        if (next_x, next_y) in self.game.vars["level_caches"]:
            cache = self.game.vars["level_caches"][(next_x, next_y)]
            print("Cache: {}".format(cache))
            newlevelobj = newlevelcls.load_from_cache(cache)
        else:
            cache = None
            newlevelobj = newlevelcls()
        new_state = DungeonState(self.game, level=newlevelobj, entry_dir=entry_dir, 
                                 player=self.player)
        if use_time_pass and cache is not None:
            for i in range(min(1000, self.game.ticks - cache["last_tick"])):
                new_state.level.update()
        if use_interlude:
            interlude = InterludeState.from_dungeon_states(self, new_state, door_dir)
            
        self.game.push_state(new_state)
        if use_interlude:
            self.game.push_state(interlude)

    def get_as_parent_surface(self):
        surface = pygame.Surface(self.game.vars["screen_size"])
        surface.fill(Color.Black)
        self.draw(surface)
        return surface

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====   Death Screen State    ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class DeathScreenState(AbstractGameState):
    def __init__(self, game):
        super().__init__(game)
        self.parent_surface = get_parent_surface(self.game)
        self.tick = 0
        self.tick_inc = 1
        self.dim = 0
        self.dim_ease_args = (0, 160, 600)
        self.last_dim = self.dim
        self.set_new_background()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:     
                    if self.tick >= self.dim_ease_args[2]:
                        self.game.pop_state()
                    else:
                        self.tick_inc = 4

    def update(self):
        self.tick += self.tick_inc
        if self.tick <= self.dim_ease_args[2]:
            self.dim = int(easing.ease_linear(self.tick, *self.dim_ease_args))
        else:
            self.dim = self.dim_ease_args[0] + self.dim_ease_args[1]

        if self.dim != self.last_dim:
            self.set_new_background()
        self.last_dim = self.dim

    def draw(self, screen):
        screen.blit(self.background, TOPLEFT)

    def set_new_background(self):
        self.background = current_as_dimmed_bg(self.game, parent_surface=self.parent_surface.copy(), dimcolor=Color.Red, dim=self.dim)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====     Interlude State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state draws the current surface and then moves
# to the next one, and thus requires 'first',
# 'second' and 'way' keyword arguments. 
# The 'way' argument is a string: either 
# "left", "right", "up" or "down".
# Note 2: "dynamic" is very slow because of the surfaces
# being constantly drawn.

class InterludeState(AbstractGameState):
    config_dungeon = json.loadf("configs/dungeon.json")
    def __init__(self, game, *, first, second, way, tick_length=300,
                                static_elems=[], drawers=[], fix=(0, 0), 
                                dynamic=False, old_state=None, new_state=None, dynamic_new_surface_delay=3):
        super().__init__(game)

        # way is from which door the player appears on the second surface

        self.first, self.second = first, second
        self.way = way
        self.tick_length = tick_length
        self.static_elems = static_elems
        self.drawers = drawers
        self.fix = fix
        self.dynamic = dynamic
        self.old_state, self.new_state = old_state, new_state
        self.dynamic_new_surface_delay_value = dynamic_new_surface_delay
        self.dynamic_new_surface_delay = self.dynamic_new_surface_delay_value
        if self.old_state is None or self.new_state is None:
            self.dynamic = False

        # Merge the two surfaces and then
        # handle the way it scrolls
        assert self.way in ("left", "right", "up", "down")
        self.surface = self.get_merged_surface(first, second, way)
        self.rect = self.surface.get_rect()

        first_w, first_h = self.first.get_size()
        second_w, second_h = self.second.get_size()
        self.tick = 0
        if self.way == "left":
            self.rect.x = 0
            self.ease_args = (0, first_w, self.tick_length)
        elif self.way == "right":
            self.rect.x = -self.second.get_width()
            self.ease_args = (-second_w, second_w, self.tick_length)
        elif self.way == "up":
            self.rect.y = 0
            self.ease_args = (0, first_h, self.tick_length)
        elif self.way == "down":
            self.rect.y = -self.second.get_height()
            self.ease_args = (-second_h, second_h, self.tick_length)

    def handle_events(self, events, pressed_keys, mouse_pos):
        if isinstance(self.new_state, DungeonState):
            self.new_state.handle_state_creation_events(events, pressed_keys, mouse_pos)

    def update(self):
        self.tick += 1
        v = easing.ease_in_out_cubic(self.tick, *self.ease_args)
        if self.way == "left":
            self.rect.x = -v
        elif self.way == "right":
            self.rect.x = v
        elif self.way == "up":
            self.rect.y = -v
        elif self.way == "down":
            self.rect.y = v
        if self.tick == self.tick_length:
            if self.way == "left":
                self.rect.x = -self.first.get_width()
            elif self.way == "right":
                self.rect.x = 0
            elif self.way == "up":
                self.rect.y = -self.first.get_height()
            elif self.way == "down":
                self.rect.y = 0

        if self.tick == self.tick_length + 1:
            self.game.pop_state()
            self.cleanup()
        elif self.dynamic:
            s1, s2, _ = self.get_dungeon_state_crops(self.old_state, self.new_state, dotopbar=False)
            if self.dynamic_new_surface_delay <= 0:
                self.get_merged_surface(s1, s2, self.way, out=self.surface)
                self.dynamic_new_surface_delay = self.dynamic_new_surface_delay_value
            else:
                self.dynamic_new_surface_delay -= 1
            self.old_state.level.update()
            self.new_state.level.update()

    def draw(self, screen):
        screen.blit(self.surface, self.rect.move(self.fix))
        for pos, surface in self.static_elems:
            screen.blit(surface, pos)
        for drawer, pos in self.drawers:
            drawer.draw(screen, pos)

    @staticmethod
    def get_merged_surface(first, second, way, out=None):
        first_w, first_h = first.get_size()
        second_w, second_h = second.get_size()
        if out is None:
            if way == "left" or way == "right":
                surface = pygame.Surface((first_w + second_w, max(first_h, second_h)))
            elif way == "up" or way == "down":
                surface = pygame.Surface((max(first_w, second_w), first_h + second_h))
        else:
            surface = out
        if way == "left":
            surface.blit(first, (0, 0))
            surface.blit(second, (first_w, 0))
        elif way == "right":
            surface.blit(second, (0, 0))
            surface.blit(first, (second_w, 0))
        elif way == "up":
            surface.blit(first, (0, 0))
            surface.blit(second, (0, first_h))
        elif way == "down":
            surface.blit(second, (0, 0))
            surface.blit(first, (0, second_h))
        return surface

    @classmethod
    def from_dungeon_states(cls, old_state, new_state, door_dir):
        ssize = old_state.game.vars["screen"].get_size()
        surface1, surface2, topbar = cls.get_dungeon_state_crops(old_state, new_state)
        interlude_way = reverse_directions[directions_base[door_dir]]
        # Save some UI elements (border, topbar).
        conf = cls.config_dungeon
        static_elems = [(conf["topbar_position"], topbar)]
        drawers = [(old_state.border_drawer, TOPLEFT)]
        return InterludeState(old_state.game, first=surface1, second=surface2, way=interlude_way, 
                              static_elems=static_elems, drawers=drawers, fix=conf["level_surface_position"],
                              old_state=old_state, new_state=new_state)

    @classmethod
    def get_dungeon_state_crops(cls, old_state, new_state, dotopbar=True):
        # Draw a frame of the game in each state (those are on different levels)
        ssize = old_state.game.vars["screen"].get_size()
        # Crops used
        conf = cls.config_dungeon
        levelcrop = pygame.Rect(conf["level_surface_position"], conf["level_surface_size"])
        topbarcrop = pygame.Rect(conf["topbar_position"], conf["topbar_size"])
        # Current (before)
        surface1 = pygame.Surface(ssize)
        old_state.draw(surface1, dplayer=False, dborder=False)
        surface1 = surface1.subsurface(levelcrop)
        # Next (after)
        surface2 = pygame.Surface(ssize)
        new_state.draw(surface2, dplayer=False, dui=True, dborder=False)
        if dotopbar:
            topbar = surface2.subsurface(topbarcrop) # The updated topbar, e.g. minimap
        else:
            topbar = None
        surface2 = surface2.subsurface(levelcrop)
        return surface1, surface2, topbar

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====   Fade Interlude State  ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class FadeInterludeState(AbstractGameState):
    def __init__(self, game, *, first, second, tick_length=100):
        super().__init__(game)
        self.first, self.second = first, second
        self.tick_length = tick_length
        self.tick = 0
        self.first.set_alpha(255)

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.tick = self.tick_length

    def update(self):
        self.first.set_alpha(255 - (self.tick / self.tick_length) * 255)
        self.tick += 1
        if self.tick > self.tick_length:
            self.first.set_alpha(0)
            self.game.pop_state()

    def draw(self, screen):
        screen.blit(self.second, TOPLEFT)
        screen.blit(self.first, TOPLEFT)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== ===== Player Inventory State  ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class PlayerInventoryState(AbstractGameState):
    lazy_state = True
    config = json.loadf("configs/player_inventory.json")
    window_size = config["window_size"]
    window_pos = config["position"]
    slots_start_pos = config["slots_start"]
    slot_size_t = config["slot_size"]
    slot_size = slot_size_t[0]
    slots_gap = config["slots_gap"]
    slot_border_width = config["slot_border_width"]
    slot_cols, slot_rows = config["slot_cols"], config["slot_rows"]
    icon_size = slot_size - (2 * slot_border_width)
    icon_size_t = (icon_size, icon_size)
    bg_tile = imglib.load_image_from_file("images/dd/env/BricksSmall.png", after_scale=(20, 20))
    border_tile = imglib.load_image_from_file("images/dd/env/Wall.png", after_scale=(20, 20))
    slot_img = imglib.load_image_from_file("images/sl/player_inv/Slot.png", after_scale=slot_size_t)
    selected_slot_img = imglib.load_image_from_file("images/sl/player_inv/SelectedSlot.png", after_scale=slot_size_t)
    pointed_slot_img = imglib.load_image_from_file("images/sl/player_inv/PointedSlot.png", after_scale=slot_size_t)
    swapping_slot_img = imglib.load_image_from_file("images/sl/player_inv/SwappingSlot.png", after_scale=slot_size_t)
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)

        self.player = self.game.player
        self.inventory = self.player.inventory

        self.surface = current_as_dimmed_bg(game, parent_surface=parent_surface, dim=125)

        self.background = imglib.repeated_image_texture(self.bg_tile, self.window_size)
        self.surface.blit(self.background, self.window_pos)
        self.background_border = imglib.image_border(self.window_size, self.border_tile)
        self.surface.blit(self.background_border, self.window_pos)

        startx, starty = self.slots_start_pos
        self.slot_positions = []
        self.item_icon_positions = []
        for row in range(self.slot_rows):
            y = starty + row * (self.slot_size + self.slots_gap)
            for col in range(self.slot_cols):
                x = startx + col * (self.slot_size + self.slots_gap)
                index = x * self.slot_cols + row
                self.surface.blit(self.slot_img, (x, y))
                self.slot_positions.append((x, y))
                xi, yi = x + self.slot_border_width, y + self.slot_border_width
                self.item_icon_positions.append((xi, yi))
        if self.player.near_container is not None:
            self.container = self.player.near_container
            self.c_slot_positions = []
            self.c_item_icon_positions = []

        self.pointed = list(divmod(self.player.selected_item_idx, self.slot_cols))[::-1]
        self.swapping_idx = None
        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_i:
                    self.leaving = True
                elif event.key == pygame.K_LEFT:
                    if self.pointed[0] > 0:
                        self.pointed[0] -= 1
                elif event.key == pygame.K_RIGHT:
                    if self.pointed[0] < self.slot_cols - 1:
                        self.pointed[0] += 1
                elif event.key == pygame.K_UP:
                    if self.pointed[1] > 0: 
                        self.pointed[1] -= 1
                elif event.key == pygame.K_DOWN:
                    if self.pointed[1] < self.slot_rows - 1:
                        self.pointed[1] += 1
                elif event.key == pygame.K_z:
                    self.player.selected_item_idx = self.pointed[0] + self.pointed[1] * self.slot_cols  
                elif event.key == pygame.K_x:
                    if self.swapping_idx is None:
                        self.swapping_idx = self.pointed[0] + self.pointed[1] * self.slot_cols
                    else:
                        s = self.player.inventory.slots
                        second_swapping_idx = self.pointed[0] + self.pointed[1] * self.slot_cols
                        s[self.swapping_idx], s[second_swapping_idx] = s[second_swapping_idx], s[self.swapping_idx]
                        self.swapping_idx = None
    def update(self):
        if self.leaving:
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        screen.blit(self.surface, TOPLEFT)        
        screen.blit(self.pointed_slot_img, self.slot_positions[self.pointed[0] + self.pointed[1] * self.slot_cols])
        if self.swapping_idx is not None:
            screen.blit(self.swapping_slot_img, self.slot_positions[self.swapping_idx])
        screen.blit(self.selected_slot_img, self.slot_positions[self.player.selected_item_idx])
        for pos, item in zip(self.item_icon_positions, self.inventory.slots):
            if item is not None and item.icon is not None:
                screen.blit(imglib.scale(item.icon, self.icon_size_t), pos)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====    Minimap View State   ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class MinimapViewState(AbstractGameState):
    lazy_state = True
    config = json.loadf("configs/minimapview.json")
    config_ui = json.loadf("configs/playerui.json")
    scroll_speed_min = 3
    scroll_speed_max = 10
    scroll_speed_acc = 0.05
    ease_to_player_length = 100
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)

        self.background = current_as_dimmed_bg(self.game, parent_surface=parent_surface, dim=125)

        self.player = self.game.player
        self.minimap = self.player.minimap

        minimap_rect = pygame.Rect(self.config_ui["minimap_pos"], self.minimap.surface.get_size())
        self.background.fill(Color.Black, minimap_rect)

        self.full = self.minimap.full_surface
        self.full_size = self.full.get_size()
        self.screen_size = self.game.vars["screen_size"]        

        self.full_rect = self.full.get_rect()
        self.view_cage_rect = pygame.Rect(self.config["view_pos"], self.config["view_size"])
        self.view_rect = self.full_rect.copy()

        self.scrolling = self.full_size[0] > self.screen_size[0] or \
                         self.full_size[1] > self.screen_size[1]

        if self.scrolling:
            self.view_rect.size = self.view_cage_rect.size
            self.set_view_rect_to_player()
            self.scroll_speed = 0
            self.xbuf, self.ybuf = self.view_rect.topleft
            self.ease_tp = False
            self.ease_tp_tick = 0
            self.ease_tp_args_x = self.ease_tp_args_y = None
        else:
            self.view_rect.center = self.view_cage_rect.center
            self.view_rect.move_ip(-self.view_cage_rect.x, -self.view_cage_rect.y)
            self.scroll_speed = self.xbuf = self.ybuf = None
            self.ease_tp = self.ease_tp_tick = self.ease_tp_args_x = self.ease_tp_args_y = None
        self.set_new_view_cage()

        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        update_cage = False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_m:
                    self.leaving = True
                if self.scrolling and event.key == pygame.K_p:
                    self.set_ease_to_player()
                    update_cage = True
        if self.scrolling:
            scr = any(pressed_keys[k] for k in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN))
            if scr:
                if self.ease_tp:
                    self.ease_tp = False
                if self.scroll_speed == 0:
                    self.scroll_speed = self.scroll_speed_min
                else:
                    self.scroll_speed += self.scroll_speed_acc
                    if self.scroll_speed > self.scroll_speed_max:
                        self.scroll_speed = self.scroll_speed_max
            if pressed_keys[pygame.K_LEFT]:
                self.xbuf -= self.scroll_speed
            if pressed_keys[pygame.K_RIGHT]:
                self.xbuf += self.scroll_speed
            if pressed_keys[pygame.K_UP]:
                self.ybuf -= self.scroll_speed
            if pressed_keys[pygame.K_DOWN]:
                self.ybuf += self.scroll_speed
            if scr:
                self.view_rect.topleft = (self.xbuf, self.ybuf)
                clamped = self.view_rect.clamp(self.full_rect)
                if self.view_rect != clamped:
                    self.view_rect = clamped
                    self.xbuf, self.ybuf = self.view_rect.topleft
                update_cage = True
            else:
                self.scroll_speed = 0
        if update_cage:
            self.set_new_view_cage()

    def update(self):
        if self.leaving:
            self.game.pop_state()
            self.cleanup()
            return
        if self.ease_tp:
            self.view_rect.centerx = easing.ease_in_out_cubic(self.ease_tp_tick, *self.ease_tp_args_x)
            self.view_rect.centery = easing.ease_in_out_cubic(self.ease_tp_tick, *self.ease_tp_args_y)
            self.xbuf, self.ybuf = self.view_rect.topleft
            self.ease_tp_tick += 1
            self.set_new_view_cage()
            if self.ease_tp_tick == self.ease_to_player_length:
                self.ease_tp = False

    def draw(self, screen):
        screen.blit(self.background, TOPLEFT)
        screen.blit(self.view_cage, self.view_cage_rect)

    def get_player_minimap_center_position(self):
        mazepos = self.game.vars["player_mazepos"]
        tile = self.minimap.minimap_tile
        mazepos_px = (mazepos[0] * tile, mazepos[1] * tile)
        return (mazepos_px[0] + tile/2, mazepos_px[1] + tile/2)

    def set_view_rect_to_player(self):            
        self.view_rect.center = self.get_player_minimap_center_position()
        self.xbuf, self.ybuf = self.view_rect.topleft

    def set_ease_to_player(self):
        px, py = self.get_player_minimap_center_position()
        vx, vy = self.view_rect.center
        self.ease_tp_args_x = (vx, px - vx, self.ease_to_player_length)
        self.ease_tp_args_y = (vy, py - vy, self.ease_to_player_length)
        self.ease_tp = True
        self.ease_tp_tick = 0

    def set_new_view_cage(self): 
        color = self.minimap.border_color
        border_drawer = imglib.ColorBorderDrawer(self.view_cage_rect.size, color, 4)
        self.view_cage = pygame.Surface(self.view_cage_rect.size)
        self.view_cage.fill(Color.Black)

        if self.scrolling:
            cut = self.full.subsurface(self.view_rect)
            self.view_cage.blit(cut, TOPLEFT)
        else:
            self.view_cage.blit(self.full, self.view_rect)
        
        border_drawer.draw(self.view_cage)


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
