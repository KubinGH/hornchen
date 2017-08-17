import abc

print("Load abstract base class of spell")

class AbstractSpell(metaclass=abc.ABCMeta):
    icon = None
    @abc.abstractmethod
    def __init__(self, player):
        self.player = player

    @abc.abstractmethod
    def cast(self):
        pass