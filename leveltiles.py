import pygame

import imglib
import json_ext as json
from abc_leveltile import AbstractLevelTile
from colors import Color

print("Load level tiles")

class TileFlags:
    Passage = 0
    EnemySpawner = 1
    RoomDoor = 2
    PartOfHiddenRoom = 3

#Imported after TileFlags definition, so that it can access it
import enemies

config = json.load(open("configs/dungeon.json", "r"))
level_size = config["level_size"]
tile_size = config["tile_size"]
tile_size_t = (tile_size, tile_size)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====       Basic Tiles       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class BaseTile(AbstractLevelTile):
    needs_update = False
    passable = True
    transparent = True
    flags = set()
    def __init__(self, level, col_idx, row_idx):
        super().__init__(level, col_idx, row_idx)

    def update(self):
        pass

    @property
    def surface(self):
        return self.drawn_surface

half_tile = tile_size // 2
half_tile_t = (half_tile, half_tile)
class MissingTile(BaseTile):
    needs_update = False
    passable = True
    transparent = True
    drawn_surface = pygame.Surface(tile_size_t)
    drawn_surface.fill((210, 0, 210))
    drawn_surface.fill(Color.Black, pygame.Rect((0, 0), half_tile_t))
    drawn_surface.fill(Color.Black, pygame.Rect((half_tile_t), (half_tile_t)))


class EmptyTile(BaseTile):
    needs_update = False
    passable = True
    transparent = True
    drawn_surface = pygame.Surface(tile_size_t)
    drawn_surface.fill(Color.Black)
    drawn_surface.set_colorkey(Color.Black)

class WallTile(BaseTile):
    needs_update = False
    passable = False
    transparent = False
    drawn_surface = imglib.load_image_from_file("images/dd/env/Wall.png", after_scale=tile_size_t)

class DoorTile(BaseTile):
    needs_update = False
    passable = True
    transparent = False
    flags = {TileFlags.Passage}
    drawn_surface = imglib.load_image_from_file("images/dd/env/DoorOnWall.png", after_scale=tile_size_t)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Room Tiles       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class HiddenRoomTile(BaseTile):
    needs_update = False
    passable = True
    transparent = False
    flags = {TileFlags.PartOfHiddenRoom}
    drawn_surface = imglib.load_image_from_file("images/dd/env/Wall.png", after_scale=tile_size_t)
    uncovered_drawn_surface = pygame.Surface(tile_size_t)
    uncovered_drawn_surface.fill(Color.Black)
    uncovered_drawn_surface.set_colorkey(Color.Black)
    def __init__(self, level, col_idx, row_idx):
        super().__init__(level, col_idx, row_idx)
        self.uncovered = False

    def uncover(self):
        self.uncovered = True
        self.drawn_surface = self.uncovered_drawn_surface
        self.transparent = True

class HiddenRoomDoorTile(HiddenRoomTile):
    drawn_surface = imglib.load_image_from_file("images/dd/env/DoorOnWall.png", after_scale=tile_size_t)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====         Spawners        ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class BaseSpawnerTile(EmptyTile):
    flags = {TileFlags.EnemySpawner}
    needs_update = True
    spawned_enemy = None
    def __init__(self, level, col_idx, row_idx):
        super().__init__(level, col_idx, row_idx)
        self.spawned = False

    def update(self):
        if not self.spawned:
            self.spawn = self.spawned_enemy(self.level, self)
            self.level.sprites.append(self.spawn)
            self.spawned = True

class GrayGooSpawner(BaseSpawnerTile):
    spawned_enemy = enemies.GrayGoo

parse_dict = {
    ".": EmptyTile,
    "W": WallTile,
    "~": DoorTile,
    ",": HiddenRoomTile,
    "-": HiddenRoomDoorTile,
    "g": GrayGooSpawner
}

passage_chars = [k for k, v in parse_dict.items() if TileFlags.Passage in v.flags]

def parse_layout(raw, level_obj):
    result = [[(parse_dict[char] if char in parse_dict else MissingTile)(level_obj, cidx, ridx)
              for cidx, char in enumerate(row)] for ridx, row in enumerate(raw)]
    assert len(result) == level_size[1], "Height of level must be equal to {}".format(level_size[1])
    assert len(result[0]) == level_size[0] and not any(len(result[0]) != len(result[i]) for i in range(len(result))), \
           "Width of level must be equal to {}".format(level_size[0])
    return result