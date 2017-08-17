import math
import time
import functools
import itertools
import random
import cProfile, pstats
import sys, gc

import pygame

import zipopen

WINDOW_SIZE = (1024, 768)
MAP_SIZE = (51, 51)
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
    for i in range(120):
        if break_loop:
            break
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                break_loop = True
                break
        screen.fill(Color.Black)
        loading_text.set_alpha(round((119-i)/119 * 255))
        screen.blit(loading_text, loading_text_rect)
        pygame.display.flip()
    screen.fill(Color.Black)
    pygame.display.flip()

# Continue initialization
import game
import fontutils
from colors import Color
from timekeeper import TimeKeeper, TValue
import gameconsole
import zipopen # The app must close the resources archive (if one is used)
# These are imported to be used by the console
import states, leveltiles, enemies, playeritems, projectiles
import imglib, fontutils, utils, particles

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
pos: {x}, {y} (center: {xc}, {yc})
"""

class App:
    console_namespace_additions = {k.__name__: k for k in
    [
        pygame, math, random, states, leveltiles, enemies, playeritems,
        projectiles, imglib, fontutils, utils, projectiles, Color, AutoProfile
    ]}
    def __init__(self, screen=None):
        self.screen = screen
        self.console = gameconsole.GameConsole(self)
        self.game = game.GameEngine(screen_size=WINDOW_SIZE, screen=self.screen, 
                                    mapsize=MAP_SIZE, app=self)
        self.running = False

    def run(self, fullscreen=fullscreen):
        last_state = current_state = None
        show_dbg = False; minim_dbg = False
        dbgfont = fontutils.get_sysfont("Monospace", 11); force_show_dbg = False
        dbgcolor = Color.Red
        def get_dbg_text_render(text):
            mtr = fontutils.get_multiline_text_render
            return mtr(dbgfont, text, antialias=False, color=dbgcolor, background=Color.Black, dolog=False, cache=False)
        max_fps_vals = itertools.cycle((0, 60, 150))
        max_fps = next(max_fps_vals)
        act_max_fps = max_fps
        # Runtime profiling
        events_time, update_time, draw_time, screenupdate_time = [TValue() for _ in range(4)]
        self.total_events_time = self.total_update_time = 0
        self.total_draw_time = self.total_screenupdate_time = 0
        self.profile_update_tick = self.profile_draw_tick = False

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
        bindings = {}
        def bind_key(key, func):
            bindings[key] = func

        # Main loop
        pause = False
        clock = pygame.time.Clock()
        self.running = True
        while self.running:
            # Event handling
            mouse_pos = pygame.mouse.get_pos()
            pressed_keys = list(pygame.key.get_pressed())
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
                    if event.key == pygame.K_F2:
                        console_enabled = not console_enabled
                        if show_dbg: force_show_dbg = True # reposition the text
                    elif event.key == pygame.K_F3:
                        show_dbg = not show_dbg
                        if show_dbg: force_show_dbg = True
                        minim_dbg = alt_pressed(pressed_keys)
                    elif event.key == pygame.K_F6:
                        if not current_state.use_mouse:
                            self.game.vars["forced_mouse"] = not self.game.vars["forced_mouse"]
                            pygame.mouse.set_visible(self.game.vars["forced_mouse"])
                    elif event.key == pygame.K_F11:
                        fullscreen = not fullscreen
                        if fullscreen:
                            flags = FULLSCREEN_FLAGS
                        else:
                            flags = NORMAL_FLAGS
                        pygame.display.set_mode(WINDOW_SIZE, flags)
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

            if console_enabled:
                if constatus is self.console.Status.Interpret:
                    namespace = locals()
                    namespace.update(self.console_namespace_additions)
                    self.console.interpret_current(namespace)
                self.console.draw(self.screen)
            if show_dbg:
                if not self.game.ticks % 30 or force_show_dbg:
                    dbg_text = ""
                    if not self.game.ticks % 90 or force_show_dbg:
                        current_fps = str(round(clock.get_fps()))
                    if not self.game.ticks % 30 or force_show_dbg:
                        _et = round(events_time.value * 10**6); _ut = round(update_time.value * 10**6)
                        _dt = round(draw_time.value * 10**6); _st = round(screenupdate_time.value * 10**6)
                    if not minim_dbg:
                        dbg_text += dbg_template.format(fps=current_fps, et=_et, ut=_ut, dt=_dt, st=_st)
                        if isinstance(current_state, states.DungeonState):
                            if not self.game.ticks % 30 or force_show_dbg:
                                _lvl = get_level()
                                _s = len(_lvl.sprites); _f = len(_lvl.friendly_sprites)
                                _h = len(_lvl.hostile_sprites); _p = len(_lvl.passive_sprites)
                                _pc = len(_lvl.particles); _x, _y = get_player().rect.topleft;
                                _xc, _yc = get_player().rect.center
                                dbg_text += dungeon_dbg_template.format(s=_s, f=_f, h=_h, p=_p, pc=_pc, 
                                                                        x=_x, y=_y, xc=_xc, yc=_yc)
                    else:
                        dbg_text += "fps: {}".format(current_fps)
                    render = get_dbg_text_render(dbg_text)
                    dbg_text_rect = render.get_rect()
                    dbg_text_rect.topleft = (0, 100) if not console_enabled else (0, 390)
                    force_show_dbg = False
                self.screen.blit(render, dbg_text_rect)

            with TimeKeeper(screenupdate_time):
                pygame.display.flip()
            self.total_screenupdate_time += screenupdate_time.value

            if current_state is not None and current_state.lazy_state:
                max_fps = 60
            else:
                max_fps = act_max_fps
            clock.tick(max_fps)
            self.game.ticks += 1

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

