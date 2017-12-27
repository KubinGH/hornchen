import math
import time
import functools
import itertools
import random
import cProfile, pstats
import os, shutil
import traceback
try:
    import cv2
    import numpy
except ImportError:
    enable_recording = False
else:
    enable_recording = True

import pygame

import zipopen # The app must close the resources archive (if one is used)
import controls

WINDOW_SIZE = (1024, 768)
MAP_SIZE = (101, 101)
MAX_FPS = 0
FULLSCREEN_FLAGS = pygame.HWACCEL | pygame.HWSURFACE | pygame.FULLSCREEN | pygame.DOUBLEBUF
NORMAL_FLAGS = pygame.HWACCEL | pygame.DOUBLEBUF

PROFILE = False

fullscreen = False

# We need to create a screen before importing so that a video mode is set,
# and we are able to .convert() images.

# Initialization
pygame.init()
print("Start loading game")
if fullscreen:
    flags = FULLSCREEN_FLAGS
else:
    flags = NORMAL_FLAGS
print("Create screen")
screen = pygame.display.set_mode(WINDOW_SIZE, flags)
screen_rect = pygame.Rect((0, 0), screen.get_size())

# "Loading..." message
try:
    loading_text_path = "images/sl/app/LoadingText.png"
    if zipopen.enable_resource_zip:
        loading_text = pygame.image.load(zipopen.open(loading_text_path, mode="rb"))
    else:
        loading_text = pygame.image.load(loading_text_path)
    loading_text_rect = pygame.Rect((0, 0), (loading_text.get_size()))
    loading_text_rect.center = screen_rect.center
except Exception as e:
    print("Failure loading animation text ({}: {})".format(type(e).__name__, str(e)))
    loading_text_shown = False
else:
    loading_text_shown = True
    screen.blit(loading_text, loading_text_rect)
    pygame.display.flip()

def make_loading_text_fade_out():
    break_loop = False
    clock = pygame.time.Clock()
    x = 20
    for i in range(x+1):
        if break_loop:
            break
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == controls.MenuKeys.Leave:
                break_loop = True
                break
        screen.fill(Color.Black)
        loading_text.set_alpha(round((x-i)/x * 255))
        screen.blit(loading_text, loading_text_rect)
        pygame.display.flip()
        clock.tick(60)
    screen.fill(Color.Black)
    pygame.display.flip()

# Continue initialization
import game
import fontutils
from colors import Color
from timekeeper import TimeKeeper, TValue
import json_ext as json
import gameconsole
# These are imported to be used by the console
# They were already imported before by children modules so there's almost no overhead
import states, leveltiles, enemies, playeritems, projectiles
import imglib, fontutils, utils, particles, pathfinding

# Runtime utilities
class AutoProfile:
    def __init__(self, name="nameless"):
        self.profiler = cProfile.Profile()
        self.name = name
    def start(self):
        self.profiler.enable()
    def stop(self, dump=False):
        self.profiler.disable()
        if dump:
            self.profiler.dump_stats(self.name + ".stats")
        stats = pstats.Stats(self.profiler)
        stats.strip_dirs(); stats.sort_stats("ncalls")
        stats.print_stats()

def fround(n):
    if n < 1:
        stripped = str(n).lstrip("0.")
        return round(n, len(stripped)-len(str(n)))
    else:
        return n

def alt_pressed(pressed_keys):
    return pressed_keys[pygame.K_LALT] or pressed_keys[pygame.K_RALT]

def shift_pressed(pressed_keys):
    return pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]

def exit_event(event, pressed_keys):
    if event.type == pygame.QUIT:
        return 1
    elif event.type == pygame.KEYDOWN and \
                (event.key in (pygame.K_q, pygame.K_F4) and alt_pressed(pressed_keys)):
        return 2
    else:
        return 0

def center_fix(outer_rect, inner_rect):
    return ((outer_rect.width - inner_rect.width) // 2, (outer_rect.height - inner_rect.height) // 2)

def fixed_mouse_pos(ds_center_fix):
    pos = pygame.mouse.get_pos()
    return (pos[0] - ds_center_fix[0], pos[1] - ds_center_fix[1])

# Debug text
dbg_template = """\
fps: {fps}
tick:
 e: {et}μs
 u: {ut}μs
 d: {dt}μs
 s: {st}μs
"""

dungeon_dbg_template = """\
sprites: {s} (f: {f} | h: {h} | p: {p})
particles: {pc}
pos: {x}, {y} (center: {xc}, {yc}) (idx: {xi}, {yi})
"""

class App:
    console_namespace_additions = {k.__name__: k for k in
    [
        pygame, math, random, states, leveltiles, enemies, playeritems,
        projectiles, imglib, fontutils, utils, projectiles, Color, AutoProfile
    ]}
    def __init__(self, screen=None):
        self._screen = self.screen = screen
        self.console = gameconsole.GameConsole(self)
        self.game = game.GameEngine(screen_size=WINDOW_SIZE, screen=self.screen,
                                    mapsize=MAP_SIZE, app=self)
        self.running = False

    def run(self, fullscreen=fullscreen):
        last_state = current_state = None
        show_dbg = False; minim_dbg = False
        dbgfont_name = "Monospace"
        dbgfont_size = 11
        self.dbgfont = fontutils.get_sysfont(dbgfont_name, dbgfont_size)
        force_show_dbg = False
        dbgcolor = Color.Red
        def get_dbg_text_render(text):
            mtr = fontutils.get_multiline_text_render
            return mtr(self.dbgfont, text, antialias=False,
                       color=dbgcolor, background=Color.Black,
                       dolog=False, cache=False)
        max_fps_vals = itertools.cycle((60, 0, 150))
        max_fps = next(max_fps_vals)
        act_max_fps = max_fps
        # Runtime profiling
        events_time, update_time, draw_time, screenupdate_time = [TValue() for _ in range(4)]
        self.total_events_time = self.total_update_time = 0
        self.total_draw_time = self.total_screenupdate_time = 0
        self.profile_update_tick = self.profile_draw_tick = False
        self.recording = False
        self.record_writer = None
        self.capture_screenshot = False
        self.enable_autoscale = False
        self._get_mouse_pos = pygame.mouse.get_pos # Overriden to scale while autoscaling
        console_enabled = False
        # Console functions
        def clear_caches():
            get = lambda mod: [getattr(mod, c) for c in dir(mod)
                               if c.endswith("_cache") and hasattr(getattr(mod, c), "clear")]
            for cache in get(imglib) + get(fontutils):
                cache.clear()
        def get_level():
            return current_state.level
        def get_player():
            return self.game.player
        def change_level(level):
            if isinstance(level, type): level = level()
            if hasattr(current_state, "level"):
                level.parent = current_state
                current_state.level = level
                get_player().level = level
            else:
                raise ValueError("Current state doesn't use a level")
        def spawn_enemy(cls, col, row, count=1):
            lvl = get_level()
            for _ in range(count):
                lvl.sprites.append(cls(lvl, lvl.layout[row][col]))
        def drop_item(item_cls, pos):
            lvl = get_level()
            lvl.sprites.append(playeritems.DroppedItem(lvl, pos, item_cls))
        def get_sprites_by_class(cls):
            return get_level().get_sprites_if(lambda sprite: type(sprite) is cls)
        def get_sprite_by_class(cls):
            return get_sprites_by_class(cls)[0]
        def give(arg):
            cls = getattr(playeritems, arg) if isinstance(arg, str) else arg
            return get_player().inventory.add_item(cls(get_player()))
        def ring_of_fire(count=360):
            l = get_level()
            c = get_player().rect.center
            P = projectiles.Fireball.from_angle
            q = 360/count
            for i in range(count):
                l.sprites.append(P(l, c, q*i))
        def test_particle(n=100):
            l = get_level()
            p = get_player()
            P = particles.Particle.from_sprite
            for i in range(n):
                l.particles.append(P(p, 5, utils.Vector.uniform(2), 300, Color.Green))
        def set_max_mana():
            get_player().mana_points = get_player().max_mana_points
        def set_max_hp():
            get_player().health_points = get_player().max_health_points
        autocalls = []
        autocalls_a = []
        bindings = {}
        if enable_recording:
            def start_record():
                self.recording = True
                self.record_writer = cv2.VideoWriter("record.mp4", 0x00000021, 60, (1024, 768), True)
            def stop_record():
                self.recording = False
                del self.record_writer
                self.record_writer = None
            bindings[pygame.K_F9] = start_record
            bindings[pygame.K_F10] = stop_record
        def autoscale(*resolution):
            """
            self.game.vars["screen"] and screen always refer to a WINDOW_SIZE
            surface that may or may not be the display, but will never change size.
            _screen always refers to the display and may have any size
            if enable_autoscale is True, otherwise it is WINDOW_SIZE.
            If enable_autoscale is False all of these values point to the same
            surface.
            """
            if fullscreen:
                return
            elif not resolution or resolution == WINDOW_SIZE or resolution == 1:
                disable_autoscale()
                return
            if len(resolution) == 1: # as scale factor
                n = resolution[0]
                resolution = (int(WINDOW_SIZE[0] * n), int(WINDOW_SIZE[1] * n))
                print(resolution)
            try:
                print("Enabling autoscale with resolution:", resolution)
                self._screen = pygame.display.set_mode(resolution, NORMAL_FLAGS)
                self.game.vars["screen"] = self.screen = pygame.Surface(WINDOW_SIZE)
                a, b = resolution, WINDOW_SIZE
                # Smaller resolution = higher f, and reverse
                f = (b[0] / a[0], b[1] / a[1])
                print("Fix factor:", f)
                def get_mouse_pos_override(*, f=f):
                    p = self._get_mouse_pos()
                    return round(f[0] * p[0]), round(f[1] * p[1])
                pygame.mouse.get_pos = get_mouse_pos_override
                self.console.erase_all()
                self.enable_autoscale = True
            except:
                print("Error while trying to enable autoscale:")
                traceback.print_exc()
                autoscale(*WINDOW_SIZE)
        def set_max_fps(v):
            global act_max_fps
            act_max_fps = v
        def disable_autoscale():
            print("Disabling autoscale")
            old_screen = pygame.display.set_mode(WINDOW_SIZE, NORMAL_FLAGS)
            self.game.vars["screen"] = self._screen = self.screen = screen
            pygame.mouse.get_pos = self._get_mouse_pos
            self.enable_autoscale = False
        def create_savefile(filename="save.json"):
            save = self.game.create_save()
            json_str = json.dumps(save)
            with open(filename, "w") as file:
                file.write(json_str)
        def load_savefile(filename="save.json"):
            assert isinstance(current_state, states.MainMenuState)
            with open(filename, "r") as file:
                save_str = file.read()
            save = json.loads(save_str)
            level = self.game.load_save(save)
            self.game.push_state(states.DungeonState(self.game, player=self.game.player, level=level, repos_player=False))

        def bind_key(key, func):
            bindings[key] = func
        def autocall(func):
            autocalls.append(func)
        def autocall_a(func):
            autocalls_a.append(func)

        def infmana():
            autocall(set_max_mana)
        def godmode():
            autocall(set_max_hp)
        def noclip():
            get_player().noclip = not get_player().noclip

        # Main loop
        pause = False
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            # Event handling
            mouse_pos = pygame.mouse.get_pos()
            pressed_keys = controls.KeyboardState(pygame.key.get_pressed())
            events = pygame.event.get()
            for event in events:
                exit_status = exit_event(event, pressed_keys)
                if exit_status != 0:
                    if exit_status == 1:
                        print("Exit from app by generic exit event")
                    elif exit_status == 2:
                        print("Exit from app by shortcut")
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == controls.DebugKeys.ToggleConsole:
                        console_enabled = not console_enabled
                        if show_dbg: force_show_dbg = True # reposition the text
                    elif event.key == controls.DebugKeys.ToggleDebug:
                        show_dbg = not show_dbg
                        if show_dbg: force_show_dbg = True
                        minim_dbg = alt_pressed(pressed_keys)
                    elif event.key == controls.DebugKeys.ToggleMouse:
                        if not current_state.use_mouse:
                            self.game.vars["forced_mouse"] = not self.game.vars["forced_mouse"]
                            pygame.mouse.set_visible(self.game.vars["forced_mouse"])
                    elif event.key == controls.DebugKeys.ToggleFullscreen:
                        fullscreen = not fullscreen
                        if fullscreen:
                            flags = FULLSCREEN_FLAGS
                        else:
                            flags = NORMAL_FLAGS
                        if self.enable_autoscale:
                            disable_autoscale()
                            pygame.display.flip()
                        self._screen = self.screen = pygame.display.set_mode(WINDOW_SIZE, flags)
                    elif event.key == controls.DebugKeys.TakeScreenshot:
                        self.capture_screenshot = True
                    elif shift_pressed(pressed_keys):
                        # These are valid characters, and the user may need them
                        # otherwise e.g. shift+p=P may be muted and a pause may be created
                        # instead
                        if not console_enabled:
                            if event.key == pygame.K_f:
                                act_max_fps = next(max_fps_vals)
                                print("Set max FPS to", act_max_fps)
                            elif event.key == pygame.K_p:
                                pause = not pause
            if pause:
                continue
            last_state = current_state
            current_state = self.game.top_state
            is_new_state = current_state is not last_state
            force_show_dbg = is_new_state or force_show_dbg

            self.game.handle_state_changes(current_state, last_state)

            # Some events (e.g. letter keypresses) are muted by the console,
            # so we need to process it first.
            if console_enabled:
                constatus = self.console.update(events, pressed_keys, mouse_pos)
            # Run after console to make sure a binding wasn't muted
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in bindings:
                    try:
                        bindings[event.key]()
                    except Exception as e:
                        print("Error executing binding {}:".format(event.key))
                        print("{}: {}".format(type(e).__name__, e))

            with TimeKeeper(events_time):
                self.game.handle_events(current_state, events, pressed_keys, mouse_pos)
                pygame.event.pump()
            self.total_events_time += events_time.value

            for func in autocalls:
                try:
                    func()
                except Exception as e:
                    print("Unhandled {} while executing autocall {}: {}".format(type(e).__name__, func.__name__, str(e)))

            # Logic

            if self.profile_update_tick:
                profile = AutoProfile("updateprofile")
                profile.start()
            with TimeKeeper(update_time):
                self.game.update(current_state)
            if self.profile_update_tick:
                profile.stop()
                del profile
                self.profile_update_tick = False
            self.total_update_time += update_time.value

            # Draw

            if self.profile_draw_tick:
                profile = AutoProfile("drawprofile")
                profile.start()
            with TimeKeeper(draw_time):
                self.game.draw(current_state, self.screen)
            if self.profile_draw_tick:
                profile.stop()
                del profile
                self.profile_draw_tick = False
            self.total_draw_time += draw_time.value

            for func in autocalls_a:
                try:
                    func()
                except Exception as e:
                    print("Unhandled {} while executing after autocall {}: {}".format(type(e).__name__, func.__name__, str(e)))

            if console_enabled:
                if constatus is self.console.Status.Interpret:
                    namespace = locals()
                    namespace.update(self.console_namespace_additions)
                    self.console.interpret_current(namespace)
                self.console.draw(self.screen)

            if show_dbg:
                # Pathfinding tests
                if isinstance(current_state, states.DungeonState):
                    levelfix = current_state.config["level_surface_position"]
                    tile = current_state.config["tile_size"]
                    a1 = get_player().closest_tile_index
                    p2 = (mouse_pos[0] - levelfix[0], mouse_pos[1] - levelfix[1])
                    a2 = (round(p2[0] / tile), round(p2[1] / tile))
                    layout = current_state.level.layout
                    if pressed_keys[pygame.K_1]:
                        t = pygame.Surface((tile, tile)).convert_alpha()
                        t.fill((255, 255, 255, 150))
                        for col, row in pathfinding.get_path_npoints(a1, a2):
                            r = layout[row][col].rect.move(levelfix)
                            self.screen.blit(t, r)
                    if pressed_keys[pygame.K_2]:
                        t = pygame.Surface((tile, tile)).convert_alpha()
                        t.fill((0, 255, 0, 150))
                        for col, row in pathfinding.a_star_in_level(a1, a2, layout):
                            r = layout[row][col].rect.move(levelfix)
                            self.screen.blit(t, r)
                if not self.game.gticks % 15 or force_show_dbg:
                    dbg_text = ""
                    if not self.game.gticks % 30 or force_show_dbg:
                        current_fps = str(round(clock.get_fps()))
                    if not self.game.gticks % 15 or force_show_dbg:
                        _et = round(events_time.value * 10**6); _ut = round(update_time.value * 10**6)
                        _dt = round(draw_time.value * 10**6); _st = round(screenupdate_time.value * 10**6)
                    if not minim_dbg:
                        dbg_text += dbg_template.format(fps=current_fps, et=_et, ut=_ut, dt=_dt, st=_st)
                        if isinstance(current_state, states.DungeonState):
                            if not self.game.gticks % 15 or force_show_dbg:
                                _lvl = get_level()
                                _s = len(_lvl.sprites); _f = len(_lvl.friendly_sprites)
                                _h = len(_lvl.hostile_sprites); _p = len(_lvl.passive_sprites)
                                _pc = len(_lvl.particles); _x, _y = get_player().rect.topleft;
                                _xc, _yc = get_player().rect.center
                                _xi, _yi = get_player().closest_tile_index
                                dbg_text += dungeon_dbg_template.format(s=_s, f=_f, h=_h, p=_p, pc=_pc,
                                                                        x=_x, y=_y, xc=_xc, yc=_yc, xi=_xi, yi=_yi)
                        if self.recording:
                            dbg_text += "(REC)\n"
                    else:
                        dbg_text += "fps: {}".format(current_fps)
                        if self.recording:
                            dbg_text += " (REC)"
                    render = get_dbg_text_render(dbg_text)
                    dbg_text_rect = render.get_rect()
                    if console_enabled:
                        p = (0, 390)
                    elif isinstance(current_state, (states.MainMenuState, states.SettingsState)):
                        p = (0, 0)
                    else:
                        p = (0, 100)
                    dbg_text_rect.topleft = p
                    force_show_dbg = False
                self.screen.blit(render, dbg_text_rect)

            with TimeKeeper(screenupdate_time):
                if self.enable_autoscale:
                    self._screen.fill(Color.Black)
                    scaled = imglib.scale(self.screen, self._screen.get_size(),
                                          docache=False, dolog=False)
                    self._screen.blit(scaled, (0, 0))
                pygame.display.flip()
            self.total_screenupdate_time += screenupdate_time.value

            if self.recording:
                array = pygame.surfarray.pixels3d(self.screen)
                array = cv2.transpose(array)[:,:,::-1]
                self.record_writer.write(array)
                del array
            if self.capture_screenshot:
                self.capture_screenshot = False
                try:
                    if not os.path.exists("screenshots"):
                        os.makedirs("screenshots")
                        screenshot_folder_exists = True
                    count = len([f for f in os.listdir("screenshots") if f.endswith(".png")])
                    name = "screenshots/Screenshot{}.png".format(count + 1)
                    if os.path.exists(name):
                        n = random.randint(1, 999)
                        name = "screenshots/Screenshot{}-{}.png".format(count + 1, n)
                    pygame.image.save(self.screen, name)
                except Exception as e:
                    print("Error capturing screenshot ({}: {})".format(type(e).__name__, str(e)))
            if current_state is not None and current_state.lazy_state:
                max_fps = 60
            else:
                max_fps = act_max_fps

            clock.tick(max_fps)
            self.game.gticks += 1

        self.game.cleanup()
        pygame.quit()
        if zipopen.archive is not None:
            zipopen.archive.close()



if __name__ == "__main__":
    print("Screen size:", WINDOW_SIZE)
    if PROFILE:
        profiler = AutoProfile("profile")
        profiler.start()
    if loading_text_shown:
        make_loading_text_fade_out()
    app = App(screen)
    app.run()
    if PROFILE:
        profiler.stop(dump=True)
