import abc

print("Load abstract base class of spell")

class AbstractSpell(metaclass=abc.ABCMeta):
    icon = None
    tree_pos = None
    mana_cost = None
    special_cast = False
    def __init__(self, player):
        self.player = player
        self.cast_this_tick = False # set by caster

    @abc.abstractmethod
    def cast(self):
        pass

    def can_cast(self, events, pressed_keys, mouse_pos, controls):
        return True

    def on_select(self):
        pass

    def on_deselect(self):
        pass