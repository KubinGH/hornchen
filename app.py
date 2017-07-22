import math
import functools
import itertools
import cProfile, pstats

import pygame

WINDOW_SIZE = (1024, 768)
MAP_SIZE = (10, 10)
MAX_FPS = 0
FULLSCREEN_FLAGS = pygame.HWACCEL | pygame.HWSURFACE | pygame.FULLSCREEN | pygame.DOUBLEBUF
NORMAL_FLAGS = pygame.HWACCEL

PROFILE = True

dbg_template = """\
fps: {fps}
tick:
 e: {et}μs
 u: {ut}μs
 d: {dt}μs
 s: {st}μs
 """

fullscreen = False 

# We need to create a screen before importing so that a video mode is set,
# and we are able to .convert() images.
pygame.init()
print("Start loading game")
if fullscreen:
    flags = FULLSCREEN_FLAGS
else:
    flags = NORMAL_FLAGS
print("Create screen")
screen = pygame.display.set_mode(WINDOW_SIZE, flags)

import game
import fontutils
from colors import Color
from timekeeper import TimeKeeper, TValue
import gameconsole
import zipopen # The app must close the archive
# These are imported to be used by the console
import states, leveltiles, enemies, playeritems, projectiles

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
    return event.type == pygame.QUIT or \
           (event.type == pygame.KEYDOWN and \
                (event.key in (pygame.K_q, pygame.K_F4) and alt_pressed(pressed_keys)))

def center_fix(outer_rect, inner_rect):
    return ((outer_rect.width - inner_rect.width) // 2, (outer_rect.height - inner_rect.height) // 2)

def fixed_mouse_pos(ds_center_fix):
    pos = pygame.mouse.get_pos()
    return (pos[0] - ds_center_fix[0], pos[1] - ds_center_fix[1])

class App:
    console_namespace_additions = {
        "pygame": pygame,
        "math": math,
        "states": states,
        "leveltiles": leveltiles,
        "enemies": enemies,
        "playeritems": playeritems,
        "projectiles": projectiles
    }
    def __init__(self, screen=None, use_dirty_rects=False):
        self.screen = screen
        self.console = gameconsole.GameConsole(self)
        self.game = game.GameEngine(screen_size=WINDOW_SIZE, screen=self.screen, 
                                    mapsize=MAP_SIZE)
        self.use_dirty_rects = use_dirty_rects

    def run(self, fullscreen=fullscreen):
        last_state = current_state = None
        show_dbg = False; dbgfont = fontutils.get_sysfont("Monospace", 16); force_show_dbg = False
        dbgcolor = Color.Red
        def get_dbg_text_render(text):
            mtr = fontutils.get_multiline_text_render
            return mtr(dbgfont, text, antialias=False, color=dbgcolor, background=None, dolog=False)
        max_fps_vals = itertools.cycle((0, 60, 150))
        max_fps = next(max_fps_vals)
        act_max_fps = max_fps
        events_time, update_time, draw_time, screenupdate_time = [TValue() for _ in range(4)]
        self.total_events_time = self.total_update_time = 0
        self.total_draw_time = self.total_screenupdate_time = 0
        self.profile_update_tick = False

        console_enabled = False
        # Console functions
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
            lev = get_level()
            fire = projectiles.Fireball
            for i in range(count):
                lev.sprites.append(fire.from_angle(lev, get_player().rect.topleft, 360/count*i))
        bindings = {}
        def bind_key(key, func):
            bindings[key] = func

        # Main loop
        pause = False
        clock = pygame.time.Clock()
        running = True
        while running:
            # Event
            mouse_pos = pygame.mouse.get_pos()
            pressed_keys = list(pygame.key.get_pressed())
            events = pygame.event.get()
            for event in events:
                if exit_event(event, pressed_keys):
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F2:
                        console_enabled = not console_enabled
                    elif event.key == pygame.K_F3:
                        show_dbg = not show_dbg
                        if show_dbg: force_show_dbg = True
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
                            elif event.key == pygame.K_h:
                                self.game.vars["enable_enemy_hp_bars"] = not self.game.vars["enable_enemy_hp_bars"]
                            elif event.key == pygame.K_p:
                                pause = not pause
            if pause:
                continue
            last_state = current_state
            current_state = self.game.top_state

            self.game.handle_state_changes(current_state, last_state)

            # Some events (e.g. letter keypresses) are muted by the console,
            # so we need to process it first.
            if console_enabled:
                constatus = self.console.update(events, pressed_keys, mouse_pos)
            # Check if a binding wasn't muted
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in bindings:
                    bindings[event.key]()

            with TimeKeeper(events_time):
                self.game.handle_events(current_state, events, pressed_keys, mouse_pos)
                pygame.event.pump()
            self.total_events_time += events_time.value


            # Logic

            if self.profile_update_tick:
                print("Run profiler")
                profiler = cProfile.Profile()
                profiler.enable()
                print("Start update")
            with TimeKeeper(update_time):
                self.game.update(current_state)
            if self.profile_update_tick:  
                print("End update")      
                profiler.disable()
                profiler.dump_stats("updateprofile.stats")
                stats = pstats.Stats("updateprofile.stats")
                stats.strip_dirs(); stats.sort_stats("ncalls")
                print("Results:")
                stats.print_stats()
                self.profile_update_tick = False
            self.total_update_time += update_time.value
            
            # Draw

            with TimeKeeper(draw_time):
                self.game.draw(current_state, self.screen)
            self.total_draw_time += draw_time.value

            if console_enabled:
                if constatus is self.console.Status.Interpret:
                    namespace = locals()
                    namespace.update(self.console_namespace_additions)
                    self.console.interpret_current(namespace)
                self.console.draw(self.screen)
            if show_dbg:
                dbg_text = ""
                # Only check tick times every 120 ticks or on debug toggle
                if not self.game.ticks % 90 or force_show_dbg:
                    current_fps = str(round(clock.get_fps()))
                if not self.game.ticks % 30 or force_show_dbg:
                    _et = round(events_time.value * 10**6); _ut = round(update_time.value * 10**6)
                    _dt = round(draw_time.value * 10**6); _st = round(screenupdate_time.value * 10**6)
                dbg_text += dbg_template.format(fps=current_fps, et=_et, ut=_ut, dt=_dt, st=_st)
                if isinstance(current_state, states.DungeonState):
                    _lvl = get_level()
                    _s = len(_lvl.sprites); _f = len(_lvl.friendly_sprites)
                    _h = len(_lvl.hostile_sprites); _p = len(_lvl.passive_sprites)
                    dbg_text += "sprites: {s} (f: {f} | h: {h} | p: {p})\n".format(s=_s, f=_f, h=_h, p=_p)
                render = get_dbg_text_render(dbg_text)
                dbg_text_rect = render.get_rect()
                dbg_text_rect.topleft = (0, 64) if not console_enabled else (0, 390)
                self.screen.blit(render, dbg_text_rect)
                force_show_dbg = False

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
        profiler = cProfile.Profile()
        profiler.enable()
    app = App(screen)
    app.run()        
    if PROFILE:
        profiler.disable()
        profiler.dump_stats("profile.stats")
        stats = pstats.Stats("profile.stats")
        stats.strip_dirs(); stats.sort_stats("ncalls")
        stats.print_stats()

