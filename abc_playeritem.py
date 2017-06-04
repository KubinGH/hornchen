import abc

class AbstractPlayerItem(metaclass=abc.ABCMeta):
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
