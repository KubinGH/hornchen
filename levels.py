import abc
from os import listdir
import re
import copy

import pygame

import imglib
import json_ext as json
from abc_level import AbstractLevel
import leveltiles
from colors import Color
import zipopen

if zipopen.enable_resource_zip:
    open = zipopen.open
    listdir = zipopen.listdir


print("Load levels")

TOPLEFT = (0, 0)

START_LEVEL_FILENAME = "start.txt"
FALLBACK_LEVEL_FILENAME = "empty.txt"
NONGENERIC_FLAG = "::nongeneric::"

config = json.loadf("configs/dungeon.json")
level_surface_size = config["level_surface_size"]
tile_size = config["tile_size"]
tile_size_t = (tile_size, tile_size)


opposite_dirs = {"left": "right", "right": "left", 
                 "top": "bottom", "bottom": "top"}

all_levels = []

def logic_xnor(first, second):
    return bool(first) is bool(second)

def get_column(array, col):
    return [array[row][col] for row in range(len(array))]

default_start_entries = {"left": None, "right":  None, 
                         "top": None, "bottom": None, "any": None}
entryany_pattern = re.compile("any=\((\d+), (\d+)\)")
bgname_pattern = re.compile("bg=\"(.+?)\"")
def load_level_data_from_file(filename, is_special=False):
    with open(filename) as file:
        lines = [line.strip() for line in file.read().strip().split("\n")]
    nongeneric_flag_present = lines[0] == NONGENERIC_FLAG
    # We either want both the flag to be present and the level to be non generic,
    # or no flag and generic level, so we use XNOR (true for 00 and 11).
    if logic_xnor(nongeneric_flag_present, is_special):
        if nongeneric_flag_present: lines.pop(0)
    else:
        raise AssertionError("Level from file {} was expected to have non generic flag.".format(filename))
    entries = default_start_entries.copy()
    matchlast = bgname_pattern.match(lines[-1])
    if matchlast is not None:
        bgtile_name = matchlast.group(1)
        lines = lines[:-1]
    else:
        bgtile_name = "images/dd/env/Bricks.png"
    matchlast = entryany_pattern.match(lines[-1])
    if matchlast is not None:
        entries["any"] = (int(matchlast.group(1)), int(matchlast.group(2)))
        lines = lines[:-1]
    seqs = (get_column(lines, 0), get_column(lines, -1), lines[0], lines[-1])
    for key, seq in zip(("left", "right", "top", "bottom"), seqs):
        for i, ch in enumerate(seq):
            if ch in leveltiles.passage_chars:
                if key == "left":   entries["left"]   = (0, i)
                if key == "right":  entries["right"]  = (len(lines[0]) - 1, i)
                if key == "top":    entries["top"]    = (i, 0)
                if key == "bottom": entries["bottom"] = (i, len(lines) - 1)
    assert all(len(line) == len(lines[0]) for line in lines)
    return lines, entries, bgtile_name


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====        Base Level       ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

class BaseLevel(AbstractLevel):
    start_entries = default_start_entries
    def __init__(self):
        super().__init__()
        self.background = imglib.repeated_image_texture(self.bg_tile, level_surface_size)
        self.current_render = pygame.Surface(level_surface_size)
        self.force_full_update = True
        self.force_render_update = True
        self.transparency_map = self.create_transparency_map() # passability for collisions
        # used if you want to save something into the cache before level deletion
        self.precache = {
            "sprites": [],
            "uncovered": [],
            "tiles": []
        }
        # This is should be set by the state that handles this level, and has a 'player' attribute
        self.parent = None

    def get_layout_copy(self):
        return leveltiles.parse_layout(self.raw_layout, self)

    @property
    def layout_size(self):
        return (self.width, self.height)

    @property
    def width(self):
        return len(self.layout[0])

    @property
    def height(self):
        return len(self.layout)

    def create_cache(self):
        cache = self.precache
        cache["sprites"].extend(sprite.create_cache() for sprite in self.sprites)
        for row, tilerow in enumerate(self.layout):
            for col, tile in enumerate(tilerow):
                if tile.flags.PartOfHiddenRoom and tile.uncovered:
                    cache["uncovered"].append((col, row))
        return cache

    @classmethod
    def load_from_cache(cls, cache):
        obj = cls()
        for sprite_cache in cache["sprites"]:
            if sprite_cache["type"] == "enemy":
                scol, srow = sprite_cache["levelpos"][0], sprite_cache["levelpos"][1]
                spawner_tile = obj.layout[srow][scol]
                sprite = sprite_cache["cls"].from_cache(obj, spawner_tile, sprite_cache)
                obj.sprites.append(sprite)
            elif sprite_cache["type"] == "item":
                obj.sprites.append(sprite_cache["cls"].from_cache(obj, sprite_cache))
        for col, row in cache["uncovered"]:
            tile = obj.layout[row][col]
            if tile.flags.PartOfHiddenRoom:
                tile.uncover()
        for tile_cache in cache["tiles"]:
            col, row = tile_cache["col"], tile_cache["row"]
            tile = obj.layout[row][col]
            # Because the layout is already created,
            # the tiles are mutated in order to load the cache.
            # (As opposed to creating a new instance from the cache)
            tile.load_cache(tile_cache)
        return obj

    def stop(self):
        return self.create_cache()

    def create_transparency_map(self):
        return [[tile.passable for tile in row] for row in self.layout]

    def update_render(self):
        self.current_render.fill(Color.Black)
        self.current_render.blit(self.background, TOPLEFT)
        for row in self.layout:
            for tile in row:
                self.current_render.blit(tile.surface, tile.rect)

    def update_full(self):
        self.create_transparency_map()
        self.update_render()

    def update(self):
        if self.force_full_update:
            self.update_full()
            self.force_full_update = False
            self.force_render_update = False
        for row in self.layout:
            for tile in row:
                if tile.needs_update:
                    tile.update()
        # The sprites may decide to remove themselves, so we need a copy
        for sprite in self.sprites[:]:
            sprite.update()

    def handle_events(self, events, pressed_keys, mouse_pos):
        pass

    def draw(self, screen, fix=TOPLEFT):
        if self.force_render_update:
            self.update_render()
            self.force_render_update = False
        screen.blit(self.current_render, fix)
        for sprite in self.sprites:
            sprite.draw(screen, fix)

# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====      Level Factory      ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

def level_creator(filename, expected_special=False):
    # The level_creator can be used for any kind of level,
    # but if expected_special is not True and the level's file
    # begins with a '::nongeneric::' line, an AssertionError will
    # be raised. If expected_special is True, the opposite will
    # happen: if there's no '::nongeneric::' line, an AssertionError
    # will be raised.
    class GenericLevel(BaseLevel):
        source = filename
        _leveldata = load_level_data_from_file(filename, is_special=expected_special)
        raw_layout, start_entries, bg_name = _leveldata
        start_entries_rev = {v: k for k, v in start_entries.items()}
        bg_tile = imglib.load_image_from_file(bg_name)
        passages = []
        for k, v in start_entries.items():
            if v is not None:
                passages.append(k)
    return GenericLevel


# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====
# ===== ===== =====         Generic         ===== ===== =====
# ===== ===== ===== ===== ===== ===== ===== ===== ===== =====

StartLevel = level_creator("levels/" + START_LEVEL_FILENAME, True)
EmptyLevel = level_creator("levels/" + FALLBACK_LEVEL_FILENAME, True)

print("Loading generic levels: ", end="")
for file in sorted(listdir("levels")):
    if not file.endswith(".txt"): continue
    try:
        level = level_creator("levels/{}".format(file))
    except Exception as e:
        if isinstance(e, AssertionError):
            # Some of the files here will be non generic levels, hence
            # an AssertionError will be raised.
            pass
        else:
            print("Error while setting up generic level from file {}.".format(file))
            print("{}: {}".format(type(e).__name__, str(e)))
    else:
        print("{}; ".format(file), end="")
        all_levels.append(level)
print("\nDone loading levels")

# A dictionary of all of the levels, with the keys being from which sides the doors
# are in the levels that are in the value (which is a list).
# For the map generator to use a level, it needs to be added here.
# 0b(...) -> left, right, up, down

leveldict = {
    0b0001: [],
    0b0010: [],
    0b0011: [],
    0b0100: [],
    0b0101: [],
    0b0110: [],
    0b0111: [],
    0b1000: [],
    0b1001: [],
    0b1010: [],
    0b1011: [],
    0b1100: [],
    0b1101: [],
    0b1110: [],
    0b1111: []
}

for level in all_levels:
    key = bool(level.start_entries["bottom"]) * 1 + bool(level.start_entries["top"]) * 2 + \
          bool(level.start_entries["right"]) * 4 + bool(level.start_entries["left"]) * 8
    leveldict[key].append(level)