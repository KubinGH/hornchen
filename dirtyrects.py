import pygame

print("Load dirty rect handler")

class DirtyRectsHandler:
    def __init__(self):
        self.current_rects = None
        self.last_rects = None

    def add(self, rect):
        if rect is not None:
            self.current_rects.append(rect)

    def add_iter(self, rects):
        if self.current_rects is not None and rects is not None:
            self.current_rects.extend(rects)
        else:
            self.current_rects = None

    def get(self):
        if self.current_rects is not None:
            yield from self.current_rects
            self.current_rects = []
            if self.last_rects is not None:
                yield from self.last_rects
            self.last_rects, self.current_rects = self.current_rects, []
        else:
            self.last_rects, self.current_rects = self.current_rects, []
            return None            

    def force_full_update(self):
        self.current_rects = None

    @property
    def rect_count(self):
        return len(self.current_rects) if self.current_rects is not None else 0 + \
               len(self.last_rects) if self.last_rects is not None else 0

class DummyRectsHandler:
    def __init__(self):
        self.current_rects, self.last_rects = [], []

    def add(self, rect):
        pass

    def add_iter(self, rects):
        pass

    def get(self):
        yield None

    def force_full_update(self):
        pass

    @property
    def rect_count(self):
        return 0
