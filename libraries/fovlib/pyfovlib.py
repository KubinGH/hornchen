"""
http://www.roguebasin.com/index.php
?title=FOV_using_recursive_shadowcasting_-_improved
According to the Java implementation
"""

import math

class Directions:
    diagonals = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    basic = [(0, -1), (0, 1), (-1, 0), (1, 0)]

class CircleStrategy:
    @staticmethod
    def radius(dx, dy):
        return math.hypot(dx, dy)

def calculate_fov(transparency_map, start_x, start_y, radius, rstrat=CircleStrategy, *, dest=None):
    width, height = len(transparency_map[0]), len(transparency_map)
    if dest is None:
        light_map = [[False for _ in range(width)] for _ in range(height)]
    else:
        light_map = dest
    light_map[start_y][start_x] = 1
    args = (light_map, start_x, start_y, radius, transparency_map, width, height, rstrat)
    for direction in Directions.diagonals:
        cast_light(1, 1.0, 0.0, 0, direction[0], direction[1], 0, args)
        cast_light(1, 1.0, 0.0, direction[0], 0, 0, direction[1], args)
    return light_map


def cast_light(row, start, end, xx, xy, yx, yy, args):
    light_map, start_x, start_y, radius, transparency_map, width, height, rstrat = args
    new_start = 0.0
    if start < end: return

    blocked = False
    distance = row - 1
    while distance <= radius and not blocked:
        distance += 1
        delta_y = delta_x = -distance
        delta_x -= 1
        while delta_x <= 0:
            delta_x += 1
            current_x = start_x + delta_x * xx + delta_y * xy
            current_y = start_y + delta_x * yx + delta_y * yy
            left_slope = (delta_x - 0.5) / (delta_y + 0.5)
            right_slope = (delta_x + 0.5) / (delta_y - 0.5)

            if not (0 <= current_x < width and 0 <= current_y < height) or \
                    start < right_slope:
                continue
            elif end > left_slope:
                break

            this_radius = rstrat.radius(delta_x, delta_y)
            if this_radius <= radius:
                #brightness = 1 - (this_radius / radius)
                light_map[current_y][current_x] = True

            if blocked:
                if not transparency_map[current_y][current_x]:
                    new_start = right_slope
                    continue
                else:
                    blocked = False
                    start = new_start
            else:
                if not transparency_map[current_y][current_x] and distance < radius:
                    blocked = True
                    cast_light(distance + 1, start, left_slope, xx, xy, yx, yy, args)
                new_start = right_slope