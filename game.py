from states import TestState, MainMenuState
from player import PlayerCharacter

class GameEngine:
    default_vars = {"screen": None, "draw_surface": None, "screen_size": None,
                    "level_caches": {}, "map": None, "enable_fov": False}
    def __init__(self, **kwargs):
        self.vars = self.default_vars.copy()
        self.vars.update(kwargs)
        self.state_stack = []
        self.player = PlayerCharacter(self)
        self.push_state_t(MainMenuState)

    @property
    def top_state(self):
        return self.state_stack[-1] if self.state_stack else None

    def cleanup(self):
        pass

    def push_state(self, state):
        print("Push state {} to the stack".format(type(state).__name__))
        self.state_stack.append(state)

    def push_state_t(self, state_type):
        print("Push state (type) {} to the stack".format(state_type.__name__))
        self.state_stack.append(state_type(self))

    def pop_state(self, i=-1):
        print("Pop state {} from the stack at index {}".format(type(self.state_stack[i]).__name__, i))
        return self.state_stack.pop(i)

    def handle_events(self, state, events, pressed_keys, mouse_pos, *args, **kwargs):
        state.handle_events(events, pressed_keys, mouse_pos, *args, **kwargs)

    def update(self, state, *args, **kwargs):
        state.update(*args, **kwargs)

    def draw(self, state, screen, *args, **kwargs):
        return state.draw(screen, *args, **kwargs)

    @property
    def states_str(self):
        return [type(state).__name__ for state in self.state_stack]