import math
import random
import warnings

import pygame

import json_ext as json
import controls
import fontutils
import imglib
from abc_state import AbstractGameState
import levels
from colors import Color
import easing
import spells

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
    def __init__(self, name, text, font, pos, is_active=lambda: True, colors=(Color.White, Color.Yellow)):
        self.name = name
        self.text, self.font = text, font
        self.pos, self.colors = pos, colors
        self.is_active = is_active
        self.text_renders = [fontutils.get_text_render(self.font, text, True, color) for color in self.colors]
        self.rect = pygame.Rect(self.pos, self.text_renders[0].get_size())
        self.hovered_over = False
        self.pressed = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        if not self.is_active: return
        self.hovered_over = self.rect.collidepoint(mouse_pos)
        self.pressed = self.hovered_over and any(event.type == pygame.MOUSEBUTTONDOWN for event in events)

    def update(self):
        if not self.is_active: return

    def draw(self, screen):
        if not self.is_active: return
        screen.blit(self.current_render, self.rect)

    @property
    def current_render(self):
        return self.text_renders[self.hovered_over]

class UIToggleButton(UIButton):
    def __init__(self, name, text, font, pos, get_value, 
                 colors=(Color.White, Color.Yellow), toggle_texts=("No", "Yes"), format_t=": {: >16}"):
        super().__init__(name, text, font, pos, colors)
        self.get_value = get_value
        self.toggle_texts = toggle_texts
        self.format_t = format_t
        self.text_renders = [[fontutils.get_text_render(self.font, self.text + self.format_t.format(tt), True, color) 
                              for color in self.colors] for tt in self.toggle_texts]
        self.rect = pygame.Rect(self.pos, self.text_renders[self.toggle_texts[1] > self.toggle_texts[0]][0].get_size())
    
    @property
    def current_render(self):
        return self.text_renders[self.get_value()][self.hovered_over]

class UISlider:
    def __init__(self, rects, length=50, fix=10, ease=easing.ease_in_out_cubic, ins=True):
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


class Camera:
    scroll_speed_min = 3
    scroll_speed_max = 10
    scroll_speed_acc = 0.05
    # Base rect coordinates are middle-based
    def __init__(self, get_pairs, view_cage, view_rect, full_rect, mid=True):
        self.get_pairs, self.view_cage_rect = get_pairs, view_cage
        self.view_rect, self.full_rect = view_rect, full_rect
        self.mid = mid
        self.middle_fix = (self.view_rect.width // 2, self.view_rect.height // 2)
        self.scroll_speed = 0
        self.dragging = self.last_dragging = False
        self.xbuf, self.ybuf = self.view_rect.topleft
        self.mouse_pos = self.last_mouse_pos = pygame.mouse.get_pos()

    def handle_moving(self, pressed_keys, mouse_pos, enable_drag):
        self.dragging = pygame.mouse.get_pressed()[0]
        ks = (controls.MenuKeys.Left, controls.MenuKeys.Right, 
              controls.MenuKeys.Up, controls.MenuKeys.Down)
        ms = enable_drag and self.dragging and self.last_dragging
        scr = any(pressed_keys[k] for k in ks) or ms
        if scr:
            if self.scroll_speed == 0:
                self.scroll_speed = self.scroll_speed_min
            else:
                self.scroll_speed += self.scroll_speed_acc
                if self.scroll_speed > self.scroll_speed_max:
                    self.scroll_speed = self.scroll_speed_max
        if pressed_keys[controls.MenuKeys.Left]:
            self.xbuf -= self.scroll_speed
        if pressed_keys[controls.MenuKeys.Right]:
            self.xbuf += self.scroll_speed
        if pressed_keys[controls.MenuKeys.Up]:
            self.ybuf -= self.scroll_speed
        if pressed_keys[controls.MenuKeys.Down]:
            self.ybuf += self.scroll_speed
        if ms:
            self.xbuf += (self.last_mouse_pos[0] - mouse_pos[0])
            self.ybuf += (self.last_mouse_pos[1] - mouse_pos[1])
        if scr:
            self.view_rect.topleft = (self.xbuf, self.ybuf)
            if self.mid:
                self.view_rect.left = max(-self.full_rect.width // 2, self.view_rect.left)
                self.view_rect.right = min(self.full_rect.width // 2, self.view_rect.right)
                self.view_rect.top = max(-self.full_rect.height // 2, self.view_rect.top)
                self.view_rect.bottom = min(self.full_rect.height // 2, self.view_rect.bottom)
            else:
                self.view_rect.left = max(0, self.view_rect.left)
                self.view_rect.right = min(self.full_rect.width, self.view_rect.right)
                self.view_rect.top = max(0, self.view_rect.top)
                self.view_rect.bottom = min(self.full_rect.height, self.view_rect.bottom)                
            self.xbuf, self.ybuf = self.view_rect.topleft
            r = True
        else:
            self.scroll_speed = 0
            r = False
        self.last_mouse_pos = mouse_pos
        self.last_dragging = self.dragging
        return r

    def draw_in_camera(self, screen, surface, rect):      
        cage_pos = self.view_cage_rect.topleft
        if self.is_viewable(rect):
            if self.is_partly_viewable(rect):
                norm = rect.move(-cage_pos[0], -cage_pos[1])
                norm.normalize()
                norm.x = -norm.x if norm.x < 0 else 0
                norm.y = -norm.y if norm.y < 0 else 0
                if rect.right > self.view_cage_rect.right:
                    norm.width -= rect.right - self.view_cage_rect.right 
                if rect.bottom > self.view_cage_rect.bottom:
                    norm.height -= rect.bottom - self.view_cage_rect.bottom
                rect.move_ip(norm.topleft)
                screen.blit(surface, rect, norm)
            else:
                screen.blit(surface, rect)

    def is_viewable(self, rect):
        return rect.colliderect(self.view_cage_rect)

    def is_partly_viewable(self, rect):
        return rect.clamp(self.view_cage_rect) != rect

    def draw(self, screen):
        vr = self.view_rect
        get_act = lambda rect: rect.move(-vr.centerx, -vr.centery).move(self.middle_fix).move(self.view_cage_rect.topleft)

        for surface, rect in self.get_pairs():
            self.draw_in_camera(screen, surface, get_act(rect))


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
    fade_length = 40
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
            UIButton("continue", "Continue", menu_font, self.config["positions"]["buttons"]["continue"]),
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
            # Reset to original pos after resuming (e.g. returning from higher states)
            button.rect.topleft = button.pos
        if self.slide_in:
            self.set_slide_in()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for button in self.button_list:
            button.handle_events(events, pressed_keys, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave:
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
        # Don't do anything if sliding
        if self.sliding_in or self.sliding_out:
            pass
        elif self.buttons["continue"].pressed:
            try:
                self.load_save()
            except FileNotFoundError:
                print("Missing save file")
        elif self.buttons["start"].pressed:
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

    def set_slide_in(self):
        self.sliding_in = True
        rects = [self.title_text_rect] + [b.rect for b in self.button_list]
        self.in_slider = UISlider(rects)

    def set_slide_out(self):
        self.sliding_out = True
        rects = [self.title_text_rect] + [b.rect for b in self.button_list]
        self.out_slider = UISlider(rects, ins=False)

    def start_game(self):
        self.game.reset_game()
        start_level = self.game.new_game()
        dungeon_state = DungeonState(self.game, level=start_level(), player=self.game.player)
        surface = dungeon_state.get_as_parent_surface()
        self.game.push_state(dungeon_state)
        self.game.push_state(FadeInterludeState(self.game, first=get_parent_surface(self.game), second=surface, tick_length=60))

    def load_save(self, filename="save.json"):
        with open(filename, "r") as file:
            save_str = file.read()
        save = json.loads(save_str)
        level = self.game.load_save(save)
        dungeon_state = DungeonState(self.game, player=self.game.player, level=level, repos_player=False)
        surface = dungeon_state.get_as_parent_surface()
        self.game.push_state(dungeon_state)
        self.game.push_state(FadeInterludeState(self.game, first=get_parent_surface(self.game), second=surface, tick_length=60))

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
            UIToggleButton("use_mouse", "Use Mouse", menu_font, self.config["positions"]["buttons"]["use_mouse"], lambda: self.game.vars["forced_mouse"]),
            UIButton("back", "Back", menu_font, self.config["positions"]["buttons"]["back"])
        ]
        self.buttons = {button.name: button for button in self.button_list}

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
                if event.key == controls.MenuKeys.Leave:
                    if self.sliding_in:
                        self.in_slider.tick = self.in_slider.length
                    elif self.sliding_out:
                        self.out_slider.tick = self.out_slider.length

    def update(self):
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

        if self.sliding_in or self.sliding_out:
            pass
        elif self.buttons["use_mouse"].pressed:
            self.game.vars["forced_mouse"] = not self.game.vars["forced_mouse"]
        elif self.buttons["back"].pressed:
            if self.slide_out:
                self.set_slide_out()
                self.after_slide_out = lambda: self.game.pop_state()

    def draw(self, screen):
        screen.blit(menu_background, TOPLEFT)
        screen.blit(self.settings_text, self.settings_text_rect)
        for button in self.button_list:
            button.draw(screen)
        menu_border_drawer.draw(screen, TOPLEFT)

    def set_slide_in(self):
        self.sliding_in = True
        rects = [self.settings_text_rect] + [b.rect for b in self.button_list]
        self.in_slider = UISlider(rects)

    def set_slide_out(self):
        self.sliding_out = True
        rects = [self.settings_text_rect] + [b.rect for b in self.button_list]
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
            UIButton("save", "Save", self.font, self.config["positions"]["buttons"]["save"]),
            UIButton("exit", "Exit", self.font, self.config["positions"]["buttons"]["exit"])
        ]
        self.buttons = {button.name: button for button in self.button_list}

        self.save_message_base = fontutils.get_text_render(menu_font, "Saved.", True, Color.Red)
        self.save_message = self.save_message_base.convert()
        self.save_message_alpha = 0

        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):        
        for button in self.button_list:
            button.handle_events(events, pressed_keys, mouse_pos)

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave:
                    self.leaving = True

    def update(self):
        for button in self.button_list:
            button.update()

        if self.buttons["return"].pressed:
            self.leaving = True
        elif self.buttons["save"].pressed:
            self.save_game()
            self.save_message_alpha = 255
        elif self.buttons["exit"].pressed:
            self.game.pop_state()
            self.cleanup()
            while not isinstance(self.game.top_state, MainMenuState):
                nxt = self.game.pop_state()
                nxt.cleanup()
            print("Level caches cleared by PauseState")
            self.game.vars["level_caches"] = {}
            return
        if self.save_message_alpha > 0:
            self.save_message = imglib.apply_alpha(self.save_message_base, self.save_message_alpha)
            self.save_message_alpha -= 4
        if self.leaving:    
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        screen.blit(self.background, TOPLEFT)
        for button in self.button_list:
            button.draw(screen)
        if self.save_message_alpha > 0:
            screen.blit(self.save_message, self.config["positions"]["save_message"])

    def save_game(self, filename="save.json"):        
        save = self.game.create_save()
        json_str = json.dumps(save)
        with open(filename, "w") as file:
            file.write(json_str)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====      Dungeon State      ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# Note: This state requires the level that will be run,
# thus it requires the 'level' and 'entry_dir' keyword arguments.
# The 'player' keyword argument should also be provided, or a new
# player will be created.

class DungeonState(AbstractGameState):
    level_state = True
    config = json.loadf("configs/dungeon.json")
    tile_size = config["tile_size"]
    pos_fix = config["level_surface_position"]
    config_ui = json.loadf("configs/playerui.json")
    def __init__(self, game, *, level, entry_dir="any", player=None, repos_player=True):
        super().__init__(game)

        self.player = player
        self.player.parent_state = self
        self.player.level = level

        self.level = level
        self.level.parent = self
        self.level.init_level()

        self.border_drawer = imglib.ColorBorderDrawer(self.game.vars["screen_size"], 
                                                      self.config["border_color"], 
                                                      self.config["border_thickness"])

        self.last_draw = False

        self.queue_state = None # Set to push a new state (if none other are pushed)

        if repos_player:
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
        new_state = False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Pause:
                    self.game.push_state(PauseState(self.game, parent_surface=gets()))
                    new_state = True; break
                elif event.key == controls.MenuKeys.PlayerInventory:
                    self.game.push_state(PlayerInventoryState(self.game, parent_surface=gets()))
                    new_state = True; break
                elif event.key == controls.MenuKeys.SpellTree:
                    self.game.push_state(SpellTreeState(self.game, parent_surface=gets()))  
                    new_state = True; break
                elif event.key == controls.MenuKeys.MinimapView:
                    self.game.push_state(MinimapViewState(self.game, parent_surface=gets()))  
                    new_state = True; break 
        if not new_state and self.queue_state:
            self.game.push_state(self.queue_state)
            self.queue_state = None


    def update(self):
        self.level.update()
        self.player.update()
        if self.game.vars["enable_death"] and self.player.health_points <= 0:
            self.game.pop_state()
            self.game.push_state(DeathScreenState(self.game, parent_surface=self.get_as_parent_surface()))
            return
        if self.player.going_through_door:
            self.player.going_through_door = False
            self.handle_level_travel()
        self.game.ticks += 1

    def draw(self, screen, *, dlevel=True, dplayer=True, dui=True, dborder=True):
        if dlevel:      
            self.level.draw(screen, self.pos_fix)
        if dplayer and not self.last_draw:     
            self.player.draw(screen, self.pos_fix)
        if dui:
            self.player.draw_ui(screen, self.pos_fix)
        if dborder:
            self.border_drawer.draw(screen, TOPLEFT)
        if self.last_draw:
            self.last_draw = False

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
        print("Player move:", (last_x, last_y), "-->", (next_x, next_y), "(direction:", direction + ")")
        opposite_dir = levels.opposite_dirs[direction]
        self.handle_next_level(last_x, last_y, next_x, next_y, direction, opposite_dir, True)

    def handle_next_level(self, last_x, last_y, next_x, next_y, door_dir, entry_dir, use_interlude=True, use_time_pass=True):
        last_x = self.game.vars["player_mazepos"][0] if last_x is None else last_x
        last_y = self.game.vars["player_mazepos"][1] if last_y is None else last_y
        self.game.vars["level_caches"][(last_x, last_y)] = self.level.create_cache()
        self.game.pop_state()
        self.cleanup()
        self.last_draw = True
        newlevelcls = self.game.vars["map"][next_y][next_x]
        self.game.vars["player_mazepos"] = (next_x, next_y)
        if newlevelcls is None:
            newlevelcls = levels.EmptyLevel
        if (next_x, next_y) in self.game.vars["level_caches"]:
            cache = self.game.vars["level_caches"][(next_x, next_y)]
            print("Next level's cache:\n{}".format(cache))
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
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)
        self.parent_surface = get_parent_surface(self.game) if parent_surface is None else parent_surface
        self.tick = 0
        self.tick_inc = 1
        self.dim = 0
        self.dim_ease_args = (0, 160, 600)
        self.last_dim = self.dim
        self.set_new_background()

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave:     
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
    def __init__(self, game, *, first, second, way, tick_length=60,
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
            if event.type == pygame.KEYDOWN and event.key == controls.MenuKeys.Leave:
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
    config = json.loadf("configs/playerinventory.json")
    window_size = config["window_size"]
    window_pos = config["position"]
    slots_start_pos = config["slots_start"]
    slot_size_t = config["slot_size"]
    slot_size = slot_size_t[0]
    slots_gap = config["slots_gap"]
    slot_border_width = config["slot_border_width"]
    slot_cols = config["slot_cols"]
    icon_size = slot_size - (2 * slot_border_width)
    icon_size_t = (icon_size, icon_size)
    container_pos_fix = (0, 2 * slot_size + slots_gap)
    item_view_icon_pos = config["item_view_icon_pos"]
    item_view_icon_size = config["item_view_icon_size"]
    item_view_name_pos = config["item_view_name_pos"]
    item_view_desc_pos = config["item_view_desc_pos"]
    font = fontutils.get_font("fonts/AnonymousPro-Regular.ttf", config["item_view_font_size"])
    font_large = fontutils.get_font("fonts/AnonymousPro-Regular.ttf", config["item_view_font_large_size"])
    bg_tile = imglib.load_image_from_file("images/dd/env/BricksSmall.png", after_scale=(20, 20))
    border_tile = imglib.load_image_from_file("images/dd/env/Wall.png", after_scale=(20, 20))
    slot_img = imglib.load_image_from_file("images/sl/player_inv/Slot.png", after_scale=slot_size_t)
    selected_slot_img = imglib.load_image_from_file("images/sl/player_inv/SelectedSlot.png", after_scale=slot_size_t)
    pointed_slot_img = imglib.load_image_from_file("images/sl/player_inv/PointedSlot.png", after_scale=slot_size_t)
    swapping_slot_img = imglib.load_image_from_file("images/sl/player_inv/SwappingSlot.png", after_scale=slot_size_t)
    def __init__(self, game, *, parent_surface=None, container=None):
        super().__init__(game)

        self.player = self.game.player
        self.inventory = self.player.inventory
        self.slot_rows = math.ceil(self.inventory.slots_count / self.slot_cols)

        self.surface = current_as_dimmed_bg(game, parent_surface=parent_surface, dim=125)

        self.background = imglib.repeated_image_texture(self.bg_tile, self.window_size)
        self.surface.blit(self.background, self.window_pos)
        self.background_border = imglib.image_border(self.window_size, self.border_tile, nowarn=True)
        self.surface.blit(self.background_border, self.window_pos)

        startx, starty = self.slots_start_pos
        self.slot_positions = []
        self.item_icon_positions = []
        for row in range(self.slot_rows):
            y = starty + row * (self.slot_size + self.slots_gap)
            for col in range(self.slot_cols):
                x = startx + col * (self.slot_size + self.slots_gap)
                self.surface.blit(self.slot_img, (x, y))
                self.slot_positions.append((x, y))
                xi, yi = x + self.slot_border_width, y + self.slot_border_width
                self.item_icon_positions.append((xi, yi))
        if container is not None or self.player.near_container is not None:
            if container is not None:
                self.container = container
            elif self.player.near_container is not None:
                self.container = self.player.near_container
            self.container.on_open(self.player)
            self.c_slot_rows = math.ceil(self.container.inventory.slots_count / self.slot_cols)
            startx, starty = self.slot_positions[0][0], self.slot_positions[-1][1]
            startx += self.container_pos_fix[0]
            starty += self.container_pos_fix[1]
            for row in range(self.c_slot_rows):
                y = starty + row * (self.slot_size + self.slots_gap)
                for col in range(self.slot_cols):
                    x = startx + col * (self.slot_size + self.slots_gap)
                    self.surface.blit(self.slot_img, (x, y))
                    self.slot_positions.append((x, y))
                    xi, yi = x + self.slot_border_width, y + self.slot_border_width
                    self.item_icon_positions.append((xi, yi))
            self.container_pointed = False
        else:
            self.container = self.container_pointed = None
            self.c_slot_rows = 0
        self.arrow_pointed = self.idx_to_pointed(self.player.selected_item_idx)
        self.pointed = self.arrow_pointed
        self.mouse_pointed = None
        self.swapping_idx = None
        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        set_select = swap = False
        # Mouse pointing
        for i, pos in enumerate(self.slot_positions):
            rect = pygame.Rect(pos, self.slot_size_t)
            if rect.collidepoint(mouse_pos):
                self.mouse_pointed = self.idx_to_pointed(i)
                break
        else:
            width = self.slot_cols * (self.slot_size_t[0] + self.slots_gap)
            height = self.slot_rows * (self.slot_size_t[1] + self.slots_gap)
            allrect = pygame.Rect(self.slot_positions[0], (width, height))
            if not allrect.collidepoint(mouse_pos):
                self.mouse_pointed = None
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave or event.key == controls.MenuKeys.PlayerInventory:
                    self.leaving = True
                elif event.key == controls.MenuKeys.Left:
                    self.arrow_pointed[0] -= 1
                elif event.key == controls.MenuKeys.Right:
                    self.arrow_pointed[0] += 1
                elif event.key == controls.MenuKeys.Up:
                    self.arrow_pointed[1] -= 1
                elif event.key == controls.MenuKeys.Down:
                    self.arrow_pointed[1] += 1
                elif event.key == controls.MenuKeys.Action1:
                    set_select = True
                elif event.key == controls.MenuKeys.Action2:
                    swap = True
            elif self.game.use_mouse and event.type == pygame.MOUSEBUTTONDOWN:
                if self.mouse_pointed is not None:
                    if event.button == 1:
                        set_select = True
                    elif event.button == 3:
                        swap = True
        if self.arrow_pointed[0] < 0:
            self.arrow_pointed[0] = 0
        elif self.arrow_pointed[0] > self.slot_cols - 1:
            self.arrow_pointed[0] = self.slot_cols - 1
        if self.arrow_pointed[1] < 0:
            self.arrow_pointed[1] = 0
        elif self.arrow_pointed[1] > self.slot_rows + self.c_slot_rows - 1:
            self.arrow_pointed[1] = self.slot_rows + self.c_slot_rows - 1
        if self.mouse_pointed is None:
            self.pointed = self.arrow_pointed
        else:
            self.pointed = self.mouse_pointed
        if set_select:        
            if self.pointed[1] < self.slot_rows:
                self.player.selected_item_idx = self.pointed_to_idx(self.pointed)
        if swap:
            if self.swapping_idx is None:
                self.swapping_idx = self.pointed.copy()
            else:
                inv1, p1 = self.get_inv_idx(self.swapping_idx)
                inv2, p2 = self.get_inv_idx(self.pointed)
                i1, i2 = self.pointed_to_idx(p1), self.pointed_to_idx(p2)
                inv1[i1], inv2[i2] = inv2[i2], inv1[i1]
                self.swapping_idx = None

    def update(self):
        if self.leaving:
            self.game.pop_state()
            self.cleanup()

    def draw(self, screen):
        screen.blit(self.surface, TOPLEFT)
        ppos = self.slot_positions[self.pointed_to_idx(self.pointed)]
        # Pointing frame
        screen.blit(self.pointed_slot_img, ppos)
        # Selection frame
        spos = self.slot_positions[self.player.selected_item_idx]
        screen.blit(self.selected_slot_img, spos)
        # Swap frame
        if self.swapping_idx is not None:
            swpos = self.slot_positions[self.pointed_to_idx(self.swapping_idx)]
            screen.blit(self.swapping_slot_img, swpos)
        # Player inventory view
        for pos, item in zip(self.item_icon_positions, self.inventory.slots):
            if item is not None and item.icon is not None:
                screen.blit(imglib.scale(item.icon, self.icon_size_t), pos)
        # Container inventory view
        if self.container is not None:
            for pos, item in zip(self.item_icon_positions[self.player.inventory.slots_count:], self.container.inventory.slots):
                if item is not None and item.icon is not None:
                    screen.blit(imglib.scale(item.icon, self.icon_size_t), pos)
        # Item view
        item_inventory, item_index = self.get_inv_idx(self.pointed)
        item = item_inventory[self.pointed_to_idx(item_index)]
        if item is not None:
            screen.blit(imglib.scale(item.icon, self.item_view_icon_size), self.item_view_icon_pos)
            item_name = item.name if item.name is not None else type(item).__name__
            name_text = fontutils.get_text_render(self.font_large, item_name, True, Color.White)
            screen.blit(name_text, self.item_view_name_pos)
            if item.description:
                lim = 24 if item.custom_word_wrap_chars is None else item.custom_word_wrap_chars
                desc_text = fontutils.get_multiline_text_render(self.font, item.description, True, Color.White, wordwrap_chars=lim)
                screen.blit(desc_text, self.item_view_desc_pos)
    
    def get_inv_idx(self, pointed):
        if pointed[1] < self.slot_rows:
            # Pointer is in player inventory
            return self.player.inventory.slots, pointed
        else:
            # Pointer is in container inventory
            return self.container.inventory.slots, (pointed[0], pointed[1] - self.slot_rows)

    def pointed_to_idx(self, pointed):
        return pointed[0] + pointed[1] * self.slot_cols

    def idx_to_pointed(self, idx):
        return list(divmod(idx, self.slot_cols))[::-1]

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
            self.ease_tp = False
            self.ease_tp_tick = 0
            self.ease_tp_args_x = self.ease_tp_args_y = None
            # The camera is used only for moving the view_rect
            self.camera = Camera(lambda: [(self.view_cage, self.view_cage_rect)], 
                                 self.view_cage_rect, self.view_rect, self.full_rect, False)
        else:
            self.view_rect.center = self.view_cage_rect.center
            self.view_rect.move_ip(-self.view_cage_rect.x, -self.view_cage_rect.y)
            self.ease_tp = self.ease_tp_tick = self.ease_tp_args_x = self.ease_tp_args_y = None
            self.camera = None
        self.set_new_view_cage()

        self.leaving = False

    def handle_events(self, events, pressed_keys, mouse_pos):
        scrolled = False
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave or event.key == controls.MenuKeys.MinimapView:
                    self.leaving = True
                if self.scrolling and event.key == controls.MenuKeys.MinimapView_MoveToPlayer:
                    self.set_ease_to_player()
                    scrolled = True
        if self.scrolling:
            scrolled_m = self.camera.handle_moving(pressed_keys, mouse_pos, self.game.use_mouse)
            scrolled = scrolled or scrolled_m
            if scrolled:
                self.set_new_view_cage()
                if scrolled_m:
                    self.ease_tp = False

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
# ===== ===== =====    Spell Tree State     ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class SpellTreeState(AbstractGameState):
    lazy_state = True
    config = json.loadf("configs/spelltree.json")
    crosshair = imglib.load_image_from_file("images/sl/ui/Crosshair.png", after_scale=(5, 5))
    small_stars = [imglib.scale(imglib.load_image_from_file("images/sl/stars/Star.png"), (i, i)) for i in range(6, 16, 2)]
    star_count = 800
    spell_icon_size = (64, 64)
    def __init__(self, game, *, parent_surface=None):
        super().__init__(game)

        self.player = self.game.player

        self.screen_size = self.game.vars["screen_size"]        
        self.full_rect = pygame.Rect((0, 0), self.config["full_size"])
        self.view_cage_rect = pygame.Rect(self.config["view_pos"], self.config["view_size"])
        vw, vh = self.config["view_size"]
        self.view_rect = pygame.Rect(-vw // 2, -vh // 2, vw, vh)
        if self.player.selected_spell is not None:
            self.view_rect.center = self.player.selected_spell.tree_pos

        self.crosshair_rect = self.crosshair.get_rect()
        self.crosshair_rect.center = self.view_cage_rect.center
        self.use_mouse = False

        self.background = current_as_dimmed_bg(self.game, parent_surface=parent_surface, dim=125)
        self.border_drawer = imglib.ColorBorderDrawer(self.view_cage_rect.size, self.player.minimap.border_color, 4)

        hfw, hfh = self.full_rect.width, self.full_rect.height
        self.stars = []
        for i in range(self.star_count):
            starrie = random.choice(self.small_stars)
            rect = starrie.get_rect()
            rect.center = (random.randint(-hfw // 2, hfw // 2), random.randint(-hfh // 2, hfh // 2))
            self.stars.append((starrie, rect))
        
        self.leaving = False

        self.spell_select = None
        self.choosing = True
        self.unlocking = True

        self.camera = Camera(self.get_surface_rect_pairs, self.view_cage_rect, self.view_rect, self.full_rect)

    def handle_events(self, events, pressed_keys, mouse_pos):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == controls.MenuKeys.Leave or event.key == controls.MenuKeys.SpellTree:
                    self.leaving = True
                elif event.key == controls.MenuKeys.Action1:
                    self.choosing = True
                elif event.key == controls.MenuKeys.Action2:
                    self.unlocking = True
        self.use_mouse = self.game.use_mouse
        self.camera.handle_moving(pressed_keys, mouse_pos, self.use_mouse)
        self.pointer = (self.view_rect.centerx, self.view_rect.centery)

    def update(self):
        if self.leaving:
            self.game.pop_state()
        select_candidates = []
        if self.use_mouse:
            mx, my = pygame.mouse.get_pos()
            mx -= self.view_cage_rect.x - self.view_rect.centerx + self.camera.middle_fix[0]
            my -= self.view_cage_rect.y - self.view_rect.centery + self.camera.middle_fix[1]
        for spell in spells.register.values():
            rect = pygame.Rect((0, 0), self.spell_icon_size)
            cx, cy = spell.tree_pos
            if self.use_mouse:
                dist = math.hypot(cx - mx, cy - my)
            else:
                dist = math.hypot(cx - self.pointer[0], cy - self.pointer[1])
            if dist < self.spell_icon_size[0] / 2:
                select_candidates.append((spell, dist))
        if select_candidates:
            select_candidates.sort(key=lambda x: x[1])
            self.spell_select = select_candidates[0][0]
        else:
            self.spell_select = None

        if self.spell_select is not None:
            unlocked_select = self.spell_select in self.player.unlocked_spells
            if self.choosing and unlocked_select and type(self.player.selected_spell) is not self.spell_select:
                print("Choose spell", self.spell_select)
                self.player.selected_spell = self.spell_select(self.player)
            elif self.unlocking and not unlocked_select:
                print("Unlock spell", self.spell_select)
                self.player.unlocked_spells.append(self.spell_select)
        self.choosing = self.unlocking = False

    def draw(self, screen):
        screen.blit(self.background, TOPLEFT)
        screen.fill(Color.Black, self.view_cage_rect)
        self.camera.draw(screen)
        if not self.use_mouse:
            screen.blit(self.crosshair, self.crosshair_rect)
        self.border_drawer.draw(screen, self.view_cage_rect.topleft)

    def get_surface_rect_pairs(self):
        result = []
        result.extend(self.stars)
            
        for spell in spells.register.values():
            unlocked = spell in self.player.unlocked_spells
            if spell is type(self.player.selected_spell):
                icon = spell.icon_circle_select
            elif spell is self.spell_select:
                icon = spell.icon_circle_select if unlocked else spell.icon_circle_dim_select
            else:
                icon = spell.icon_circle if unlocked else spell.icon_circle_dim
            icon = imglib.scale(icon, self.spell_icon_size)
            rect = icon.get_rect()
            rect.center = spell.tree_pos
            result.append((icon, rect))

        return result
