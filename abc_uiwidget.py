import abc

class AbstractUIWidget(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, game, player):
        self.game, self.player = game, player

    @abc.abstractmethod
    def update(self):
        pass

    @abc.abstractmethod
    def draw(self, screen):
        pass

    def update_on_new_level(self):
        pass

    def update_on_player_damage(self):
        pass