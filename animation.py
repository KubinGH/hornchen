import itertools
import pygame

print("Load animation")

class Animation:
    def __init__(self, frames, tick):
        self.frames, self.tick = frames, tick
        self.frame_cycle = itertools.cycle(self.frames)
        self.surface = next(self.frame_cycle)
        self.ticks_left = self.tick

    def update(self):
        if self.ticks_left == 0:
            self.surface = next(self.frame_cycle)
            self.ticks_left = self.tick
        else:
            self.ticks_left -= 1

    @classmethod
    def from_surface_w(source, frame_width, tick):
        width, height = source.get_size()
        frames = [source.subsurface(x, 0, frame_width, height)
                  for x in range(0, width, frame_width)]
        return Animation(frames, tick)

    @classmethod
    def from_surface_h(source, frame_height, tick):
        width, height = source.get_size()
        frames = [source.subsurface(0, y, width, frame_height)
                  for y in range(0, height, frame_height)]
        return Animation(frames, tick)