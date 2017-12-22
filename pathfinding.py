import collections

import pygame

import json_ext as json
import utils

config_dungeon = json.loadf("configs/dungeon.json")
level_size = config_dungeon["level_size"]
tile_size = config_dungeon["tile_size"]
tile_size_t = (tile_size, tile_size)
screen_size = config_dungeon["level_surface_size"]
screen_rect = pygame.Rect((0, 0), screen_size)

def get_path_npoints(a1, a2):
    if a1 == a2:
        return [a1]
    points = utils.line_npoints(a1, a2)
    # I'm so sorry.
    if len(points) > 2 and utils.Vector.from_points(a1, a2).to_angle() % 90 != 0:
        for p in points.copy()[1:-1]:
            points.extend(tile_neighbours(*p))
    points = sorted(set(points))
    points = [(x, y) for x, y in points if 0 <= x < level_size[0] and 0 <= y < level_size[1]]
    return points

def get_sprite_path_npoints(sprite, target_sprite):
    a1, a2 = sprite.closest_tile_index, target_sprite.closest_tile_index
    return get_path_npoints(a1, a2)

def valid_tile_index(col, row):
    return 0 <= col < level_size[0] and 0 <= row < level_size[1]

def tile_neighbours(col, row):
    result = [(col + 1, row), (col - 1, row), (col, row + 1), (col, row - 1)]
    return [p for p in result if valid_tile_index(*p)]

# Disallows impassable tiles as neighbours
# Also returns diagonals if the tiles in the base directions are passable too
# x G Diagonal prohibited
# S .
# . G Diagonal allowed
# S .
def tile_neighbours_in_level(col, row, layout):
    result = tile_neighbours(col, row)
    result = [p for p in result if layout[p[1]][p[0]].passable]
    left = layout[row][col - 1].passable if col > 0 else False
    right = layout[row][col + 1].passable if col < level_size[0] - 1 else False
    up = layout[row - 1][col].passable if row > 0 else False
    down = layout[row + 1][col].passable if row < level_size[1] - 1 else False
    if up and left and layout[row - 1][col - 1].passable:
        result.append((col - 1, row - 1))
    if down and left and layout[row + 1][col - 1].passable:   
        result.append((col - 1, row + 1))
    if up and right and layout[row - 1][col + 1].passable:    
        result.append((col + 1, row - 1))
    if down and right and layout[row + 1][col + 1].passable:  
        result.append((col + 1, row + 1))
    return result

# Designed to work with the default level layout (32x16 grid)
# if used outside: change get_neighbours
# A* Search Algorithm
# https://en.wikipedia.org/wiki/A*_search_algorithm
def a_star(start, goal, *, heuritistic=utils.dist, get_neighbours=tile_neighbours):
    closed = set()
    opened = {start}
    came_from = {}
    g_score = collections.defaultdict(lambda: float("inf"))
    g_score[start] = 0
    f_score = collections.defaultdict(lambda: float("inf"))
    f_score[start] = heuritistic(start, goal)
    while opened:
        current = min(opened, key=lambda x: f_score[x])
        if current == goal:
            return a_star_reconstruct_path(came_from, current)
        opened.remove(current)
        closed.add(current)
        for neighbour in get_neighbours(current[0], current[1]):
            if neighbour in closed:
                continue
            if neighbour not in opened:
                opened.add(neighbour)
            tentative_g_score = g_score[current] + utils.dist(current, neighbour)
            if tentative_g_score >= g_score[neighbour]:
                continue
            came_from[neighbour] = current
            g_score[neighbour] = tentative_g_score
            f_score[neighbour] = g_score[neighbour] + heuritistic(neighbour, goal)
    return []

def a_star_reconstruct_path(came_from, current):
    path = [current]
    while current in came_from.keys():
        current = came_from[current]
        path.append(current)
    return path

def a_star_in_level(start, goal, layout):
    def get_neighbours(col, row):
        return tile_neighbours_in_level(col, row, layout)
    return a_star(start, goal, get_neighbours=get_neighbours)