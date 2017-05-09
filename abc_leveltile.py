import pygame
import abc
import json_ext as json

print("Load abstract base class of level tile")

config = json.load(open("configs/dungeon.json", "r"))
level_size = config["level_size"]
tile_size = config["tile_size"]
tile_size_t = (tile_size, tile_size)

class AbstractLevelTile(metaclass=abc.ABCMeta):
    needs_update = None
    passable = None
    @abc.abstractmethod
    def __init__(self, level, col_idx, row_idx):
        """
        Initialize this tile.
        """
        self.level = level
        self.col_idx, self.row_idx = col_idx, row_idx
        self.rect = pygame.Rect((self.col_idx * tile_size, self.row_idx * tile_size), tile_size_t)

    @abc.abstractmethod
    def update(self):
        """
        Update this tile. Called every tick.
        """

    @property
    @abc.abstractmethod
    def surface(self):
        """
        Return the current surface (appearance)
        of this tile. Called when the level is drawn.
        Should be defined as a property.
        """

    @property
    def index(self):
        return self.col_idx, self.row_idx