include "cyrandom.pyx"

import itertools, collections, time
from heapq import heappush, heappop
#from random import randint, shuffle

randint = c_randint
shuffle = c_shuffle

cdef tuple zipsum(tuple first, tuple second):
    return (first[0] + second[0], first[1] + second[1])

cdef tuple random_pop(list lst):
    if len(lst) == 1:
        return lst.pop(0)
    else:
        return lst.pop(randint(0, len(lst) - 1))

cdef enum CreationStates:
    START = 0
    DONE = 1

cdef tuple DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
cdef tuple DIRS_DIAG = ((1, 1), (1, -1), (-1, -1), (-1, 1))

cdef class MazeGenerator:
    cdef readonly int width, height, sparsiness
    cdef readonly list data
    cdef readonly tuple start_pos
    cdef readonly bint enable_random_stack_pop

    def __init__(self, int width, int height, int sparsiness=2, bint random_pop=True):
        assert width > 3 and height > 3
        self.width, self.height = width, height
        self.data = []
        self.fill_data(0)
        if sparsiness < 2:
            sparsiness = 2
        self.sparsiness = sparsiness
        self.start_pos = (None, None)
        self.enable_random_stack_pop = random_pop

    def __repr__(self):
        return "MazeGenerator({}, {})".format(self.width, self.height) 

    cpdef void pprint(self):
        print("MazeGenerator {")
        print("Data:")
        for row in self.data:
            print("\t", end="")
            print(*row, sep=" ")
        print("}")

    cdef void fill_data(self, int obj):
        self.data = [[obj for _ in range(self.width)] for _ in range(self.height)]

    cdef int count_neighbouring_walls(self, int x, int y):
        return sum(bool(self.data[iy][ix]) for ix, iy in (zipsum(d, (x, y)) for d in DIRS_DIAG))

    cdef bint is_border_wall(self, int x, int y):
        return any((x == 0 and 0 <= y < self.height,
                    x == self.width - 1 and 0 <= y < self.height,
                    y == 0 and 0 <= x < self.width,
                    y == self.width - 1 and 0 <= x < self.width))

    cdef bint is_in_bounds(self, int x, int y):
        return 0 <= x < self.width and 0 <= y < self.height

    cdef bint can_be_maze_part(self, int x, int y):
        cdef int w = self.width, h = self.height
        return (0 <= x < w and 0 <= y < h and \
                not((x == 0 and 0 <= y < h) or \
                    (x == w - 1 and 0 <= y < h) or \
                    (y == 0 and 0 <= x < w) or \
                    (y == w - 1 and 0 <= x < w)))

    cpdef list next_to_uni(self, int x, int y, tuple dirs=DIRS):
        cdef tuple t = (x, y)
        cdef list result = []
        cdef tuple d, cur
        cdef int cx, cy
        for d in dirs:
            cur = zipsum(t, d)
            cx, cy = cur[0], cur[1]
            if 0 <= cx < self.width and 0 <= cy < self.height and \
                not any((cx == 0 and 0 <= cy < self.height, 
                         cx == self.width - 1 and 0 <= cy < self.height, 
                         cy == 0 and 0 <= cx < self.width, 
                         cy == self.width - 1 and 0 <= cx < self.width)):
                result.append(cur)
        return result

    cpdef list next_to(self, int x, int y):
        cdef list result = []
        if self.can_be_maze_part(x + 1, y):
            result.append((x + 1, y))
        if self.can_be_maze_part(x - 1, y):
            result.append((x - 1, y))
        if self.can_be_maze_part(x, y + 1):
            result.append((x, y + 1))
        if self.can_be_maze_part(x, y - 1):
            result.append((x, y - 1))
        return result

    cpdef list next_to_diag(self, int x, int y):
        cdef list result = []
        if self.can_be_maze_part(x + 1, y + 1):
            result.append((x + 1, y + 1))
        if self.can_be_maze_part(x - 1, y + 1):
            result.append((x - 1, y + 1))
        if self.can_be_maze_part(x - 1, y - 1):
            result.append((x - 1, y - 1))
        if self.can_be_maze_part(x + 1, y - 1):
            result.append((x + 1, y - 1))
        return result

    def create(self, start_pos=None):
        if start_pos is None:
            self.start_pos = (self.width // 2, self.height // 2)
        else:
            self.start_pos = start_pos
        tick_counter = itertools.count(1)
        self.fill_data(1)
        yield (next(tick_counter), CreationStates.START)

        cdef list start_nxt, to_visit, changed
        cdef list next_to_d, next_to, next_to_all
        cdef set visited
        cdef tuple current
        cdef int part_next_d
        if self.enable_random_stack_pop:
            vpop = lambda seq: random_pop(seq)
        else:
            vpop = lambda seq: list.pop(seq, -1)
        start_nxt = self.next_to(self.start_pos[0], self.start_pos[1])
        to_visit = []
        to_visit.extend(start_nxt)
        visited = set(start_nxt)
        while to_visit:
            current = vpop(to_visit)
            changed = []
            cx, cy = current
            next_to_d = self.next_to_diag(cx, cy)
            next_to = self.next_to(cx, cy)
            next_to_all = next_to + next_to_d
            part_next_d = 0
            for n in next_to_all:
                if not self.data[n[1]][n[0]]:
                    part_next_d += 1

            if part_next_d <= self.sparsiness:
                self.data[cy][cx] = 0
                changed.append(current)
                shuffle(next_to)
                for nxt in next_to:
                    if nxt not in visited:
                        to_visit.append(nxt)
                        visited.add(nxt)
            if changed:
                yield (next(tick_counter), changed)

        changed = []
        for col, row in start_nxt + [self.start_pos]:
            if self.data[row][col]:
                self.data[row][col] = 0
                changed.append((col, row))
        if changed:
            yield (next(tick_counter), changed)

        yield (next(tick_counter), CreationStates.DONE)

    def create2(self):
        for tick in self.create():
            pass