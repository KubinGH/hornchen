import abc

print("Load abstract base class of player item")

class AbstractPlayerItem(metaclass=abc.ABCMeta):
    icon = None
    name = None
    description = None
    custom_word_wrap_chars = None 
    dropped_size = (24, 24)
    special_use = False
    def __init__(self, player):
        self.player = player

    # Because items may have passive abilities or only
    # be cosmetic, these methods are virtual.

    def use(self):
        pass

    def handle_events(self, events, pressed_keys, mouse_pos):
        pass

    def update(self):
        pass

    def draw(self, screen, pos_fix=(0, 0)):
        pass

    def create_cache(self):
        return {"type": type(self)}

    @classmethod
    def from_cache(self, player, cache):
        return cache["type"](player)

    def can_use(self, events, pressed_keys, mouse_pos, controls):
        return True
