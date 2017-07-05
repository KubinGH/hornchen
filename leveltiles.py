import enum

import pygame

import imglib
import json_ext as json
from abc_leveltile import AbstractLevelTile
from colors import Color
import enemies
from inventory import BaseInventory

print("Load level tiles")

class TileFlags(enum.Enum):
    Passage = 0
    EnemySpawner = 1
    RoomDoor = 2
    PartOfHiddenRoom = 3
    Container = 4

class FlagSet:
    def __init__(self, *flags):
        self.flagset = set(flags)
        self.nameset = set(flag.name for flag in flags)
        # Attribute-based access
        for name in TileFlags.__members__:
            setattr(self, name, name in self.nameset)

    def copy(self):
        return FlagSet(*self.flagset)

config = json.loadf("configs/dungeon.json")
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
    flags_template = FlagSet()
    def __init__(self, level, col_idx, row_idx):
        super().__init__(level, col_idx, row_idx)
        self.flags = self.flags_template.copy()

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
    flags_template = FlagSet(TileFlags.Passage)
    drawn_surface = imglib.load_image_from_file("images/dd/env/DoorOnWall.png", after_scale=tile_size_t)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Room Tiles       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class HiddenRoomTile(BaseTile):
    needs_update = False
    passable = True
    transparent = False
    flags_template = FlagSet(TileFlags.PartOfHiddenRoom)
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
    needs_update = True
    spawned_enemy = None
    flags_template = FlagSet(TileFlags.EnemySpawner)
    def __init__(self, level, col_idx, row_idx):
        super().__init__(level, col_idx, row_idx)
        self.spawned = False

    def update(self):
        if not self.spawned:
            self.spawn = self.spawned_enemy(self.level, self)
            self.level.sprites.append(self.spawn)
            self.spawned = True
            self.level.precache["tiles"].append({
                "col": self.col_idx,
                "row": self.row_idx,
                "spawned": True,
            })

    def load_cache(self, cache):
        self.spawned = cache["spawned"]
        # Retain the cache
        self.level.precache["tiles"].append(cache)

class GrayGooSpawner(BaseSpawnerTile):
    spawned_enemy = enemies.GrayGoo


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Containers       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class BaseContainer(BaseTile):
    needs_update = False
    passable = True
    flags_template = FlagSet(TileFlags.Container)
    # Don't change this
    inventory_slots = 8
    def __init__(self, level, col_idx, row_idx, *, inventory_contents=[]):
        super().__init__(self, level, col_idx, row_idx)
        self.inventory = BaseInventory()
        # inventory_contents should be a list of item classes.
        # They are initialized when taken from the inventory
        # by a player.
        for item in inventory_contents:
            self.inventory.add_item(item)

    def take_item(self, arg, player):
        # if the item is not yet initialized (never taken by a player)
        if arg not in self.inventory.slots:
            return None
        if isinstance(arg, type):
            item_constructor = arg
            self.inventory.remove_item(item_constructor)
            return item_constructor(player)
        else:
            item = arg
            self.inventory.remove_item(item)
            return item

    def place_item(self, item):
        return self.inventory.add_item(item)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====          Parser         ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
parse_dict = {
    ".": EmptyTile,
    "W": WallTile,
    "~": DoorTile,
    ",": HiddenRoomTile,
    "-": HiddenRoomDoorTile,
    "g": GrayGooSpawner
}

# We use flags_template since these are classes
passage_chars = [k for k, v in parse_dict.items() if v.flags_template.Passage]

def parse_layout(raw, level_obj):
    result = [[(parse_dict[char] if char in parse_dict else MissingTile)(level_obj, cidx, ridx)
              for cidx, char in enumerate(row)] for ridx, row in enumerate(raw)]
    assert len(result) == level_size[1], "Height of level must be equal to {}".format(level_size[1])
    assert len(result[0]) == level_size[0] and not any(len(result[0]) != len(result[i]) for i in range(len(result))), \
           "Width of level must be equal to {}".format(level_size[0])
    return result