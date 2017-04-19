import abc
import os
import re

import pygame

import imglib
import json_ext as json
from abc_level import AbstractLevel
import leveltiles
from colors import Color

TOPLEFT = (0, 0)

START_LEVEL_FILENAME = "start.txt"

config = json.load(open("configs/dungeon.json", "r"))
level_surface_size = config["level_surface_size"]
tile_size = config["tile_size"]
tile_size_t = (tile_size, tile_size)


opposite_dirs = {"left": "right", "right": "left", 
                 "top": "bottom", "bottom": "top"}

all_levels = []

def get_column(array, col):
    return [array[row][col] for row in range(len(array))]

default_start_entries = {"left": None, "right":  None, 
                         "top": None, "bottom": None, "any": None}
entryany_pattern = re.compile("any=\((\d+), (\d+)\)")
bgname_pattern = re.compile("bg=\"(.+?)\"")
def load_level_data_from_file(filename, is_special=False):
    with open(filename, "r") as file:
        lines = file.read().strip().split("\n")
    if lines[0] == "::nongeneric::": 
        if not is_special:
            raise AssertionError
        else:
            lines = lines[1:]
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

class BaseLevel(AbstractLevel, metaclass=abc.ABCMeta):
    start_entries = default_start_entries
    def __init__(self):
        super().__init__()
        self.background = imglib.repeated_image_texture(self.bg_tile, level_surface_size)
        self.current_render = pygame.Surface(level_surface_size)
        self.force_full_update = True
        self.force_render_update = True
        self.transparency_map = self.create_transparency_map()

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
        return {}

    @classmethod
    def load_from_cache(cls, cache):
        return cls()

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
        for sprite in self.sprites:
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

def level_creator(filename):
    class GenericLevel(BaseLevel):
        source = filename
        raw_layout, start_entries, bg_name = load_level_data_from_file(filename, is_special=False)
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

start_level = None
print("Loading generic levels: ", end="")
for file in sorted(os.listdir("levels")):
    if not file.endswith(".txt"): continue
    try:
        level = level_creator("levels/{}".format(file))
    except:
        pass
    else:
        print("{}; ".format(file), end="")
        if file == START_LEVEL_FILENAME:
            start_level = level
        else:
            all_levels.append(level)
print("\nDone loading")
assert start_level is not None, "Valid start level could not be found (expected to be in levels/{})".format(START_LEVEL_FILENAME)


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