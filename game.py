import copy

import pygame

from states import MainMenuState
import mazegen, mapgen
from player import PlayerCharacter
import controls

print("Load game engine")

def log(*args, **kwargs):
    args = ("[game]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

class GameEngine:
    default_vars = {
        "DEBUG": True,
        "screen": None, "draw_surface": None, "screen_size": None,
        "level_caches": {}, "map": None, 
        "maze": None, "player_mazepos": None,
        "enable_fov": False, "forced_mouse": True,
        "enable_death": False
    }
    def __init__(self, **kwargs):
        self.vars = self.default_vars.copy()
        self.vars.update(kwargs)
        self.state_stack = []
        self.gticks = 0 # Global ticks
        self.ticks = 0  # Game ticks, active playing time (not paused or in menus)
        self.player = None
        self.reset_game()
        self.push_state(MainMenuState(self, fade_in=True))

    def reset_game(self):
        self.player = PlayerCharacter(self)
        self.vars["level_caches"].clear()

    def new_game(self):
        gen = mazegen.MazeGenerator(*self.vars["mapsize"])
        gen.create2()
        gen.pprint(prettier=True)
        self.vars["maze"] = gen.data
        self.vars["player_mazepos"] = gen.start_pos
        self.vars["map"] = [[None for _ in range(gen.width)] for _ in range(gen.height)]
        mapgen.generate_map(self.vars["map"], gen)
        start_level = self.vars["map"][gen.start_pos[1]][gen.start_pos[0]]
        return start_level

    @property
    def top_state(self):
        return self.state_stack[-1] if self.state_stack else None

    def cleanup(self):
        pass

    def push_state(self, state):
        log("Push state {} to the stack".format(type(state).__name__))
        self.state_stack.append(state)

    def push_state_t(self, state_type):
        log("Push state (type) {} to the stack".format(state_type.__name__))
        self.state_stack.append(state_type(self))

    def pop_state(self, i=-1):
        log("Pop state {} from the stack at index {}".format(type(self.state_stack[i]).__name__, i))
        return self.state_stack.pop(i)

    def handle_state_changes(self, current_state, last_state):
        if current_state is None: 
            raise RuntimeError("No current state")
        if last_state != current_state and last_state is not None and not last_state.deactivated:
            last_state.pause()
        if current_state.paused:
            current_state.resume()

    def handle_events(self, state, events, pressed_keys, mouse_pos, *args, **kwargs):
        state.handle_events(events, controls.KeyboardState(pressed_keys), mouse_pos, *args, **kwargs)

    def update(self, state, *args, **kwargs):
        state.update(*args, **kwargs)

    def draw(self, state, screen, *args, **kwargs):
        return state.draw(screen, *args, **kwargs)

    @property
    def states_str(self):
        return [type(state).__name__ for state in self.state_stack]

    @property
    def use_mouse(self):
        b = pygame.mouse.set_visible(False)
        pygame.mouse.set_visible(b)
        return b

    def create_save(self):
        cache = {}

        dstate = [s for s in self.state_stack if s.level_state]
        # Save the current level into the cache
        level_caches = self.vars["level_caches"]
        if dstate:
            level_caches = level_caches.copy()
            current_level = dstate[0].level
            level_caches[self.vars["player_mazepos"]] = current_level.create_cache()
        cache["level_caches"] = level_caches

        cache["player"] = self.player.create_cache()
        cache["player_mazepos"] = self.vars["player_mazepos"]

        cache["maze"], cache["map"] = self.vars["maze"], self.vars["map"]
        cache["enable_fov"], cache["enable_death"] = self.vars["enable_fov"], self.vars["enable_death"]
        cache["forced_mouse"] = self.vars["forced_mouse"]
        cache["ticks"], cache["gticks"] = self.ticks, self.gticks

        return cache

    def load_save(self, cache):
        self.ticks, self.gticks = cache["ticks"], cache["gticks"]
        varkeys = [k for k in self.vars.keys() if k in cache and k not in ("player",)]
        for key in varkeys:
            self.vars[key] = cache[key]
        self.player = PlayerCharacter(self)
        self.player.load_cache(cache["player"])
        mx, my = self.vars["player_mazepos"]
        level =  self.vars["map"][my][mx].load_from_cache(self.vars["level_caches"][(mx, my)])
        return level