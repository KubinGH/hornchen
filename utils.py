import pygame
import math
import random
import collections
import functools

print("Load utilities")

# Angles:
# 0 is right-hand side, increases clockwise

# Vector math

class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):
        return "Vector({}, {})".format(self.x, self.y)

    def __eq__(self, other):
        return isinstance(other, Vector) and self.x == other.x and self.y == other.y

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        return Vector(self.x + other, self.y + other)
    __radd__ = __add__

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        return Vector(self.x - other, self.y - other)
    __rsub__ = __sub__

    def __mul__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x * other.x, self.y * other.y)
        return Vector(self.x * other, self.y * other)
    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x / other.x, self.y / other.y)
        return Vector(self.x / other, self.y / other)
    __rtruediv__ = __truediv__

    def as_list(self):
        return [self.x, self.y]

    def __getitem__(self, key):
        return self.as_list()[key]

    def __iter__(self):
        return iter(self.as_list())

    def dot_product(self, other):
        return self.x * other.x + self.y * other.y

    def cross_product(self, other):
        return self.x * other.x - self.y * other.y

    @classmethod
    def from_points(cls, p1, p2):
        return cls(p1[0] - p2[0], p1[1] - p2[1])

    @classmethod
    def random_norm(cls):
        return cls.from_angle(random.randint(1, 360))

    @classmethod
    def uniform(cls, u):
        return cls(random.uniform(-u, u), random.uniform(-u, u))

    @classmethod
    def from_angle(cls, angle):
        if   angle == 0:
            return Vector(1, 0)
        elif angle == 90:
            return Vector(0, 1)
        elif angle == 180:
            return Vector(-1, 0)
        elif angle == 360:
            return Vector(0, -1) 
        else:
            radangle = math.radians(angle)
            return Vector(math.cos(radangle), math.sin(radangle))

    @property
    def magnitude(self):
        return math.sqrt(self.x ** 2 + self.y ** 2)

    def normalize(self):
        m = self.magnitude
        if m == 0:
            return Vector(0, 0)
        return Vector(self.x / m, self.y / m)

    def to_angle(self):
        angle = math.degrees(math.atan2(self.y, self.x))
        return angle if angle >= 0 else 360 + angle

    def opposite(self):
        return self * -1

    @classmethod
    def random_spread(cls, source, spread):
        val = random.randint(-spread, spread)
        p_angle = (source.to_angle() + val) % 360
        return cls.from_angle(p_angle)

    def perpendiculars(self):
        # Clockwise, Counter-Clockwise
        return [Vector(-self.y, self.x), Vector(self.y, -self.x)]

# Math

def convert_args_to_vectors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*[Vector(*a) for a in args], **kwargs)
    return wrapper

def sign(n):
    if n > 0:
        return 1
    elif n < 0:
        return -1
    else:
        return 0

def dist(c1, c2):
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1])

def point_move(a, b):
    return (a[0] + b[0], a[1] + b[1])

def rectpoints(spoint, length, width):
    sx, sy = spoint
    sidevec = length.normalize() * width / 2
    per = sidevec.perpendiculars()
    p1 = (sx + per[0].x, sy + per[0].y)
    p2 = (sx + per[1].x, sy + per[1].y)
    p3 = (p1[0] + length.x, p1[1] + length.y)
    p4 = (p2[0] + length.x, p2[1] + length.y)
    return (p1, p2, p4, p3)

def linear_function(a, b):
    return lambda x: a*x + b

@convert_args_to_vectors
def line_eq_from_points(p1, p2):
    if p1.x > p2.x: p1, p2 = p2, p1
    a = (p2.y - p1.y) / (p2.x - p1.x)
    b = (p1.y - (a * p1.x))
    return a, b

@convert_args_to_vectors
def line_collide(f1, f2, g1, g2):
    if f1.x > f2.x: f1, f2 = f2, f1
    if g1.x > g2.x: g1, g2 = g2, g1
    if f1.x == f2.x:
        return g1.x <= f1.x <= g2.x
    elif g1.x == g2.x:
        return f1.x <= g1.x <= f2.x 
    f_a, f_b = line_eq_from_points(f1, f2)
    g_a, g_b = line_eq_from_points(g1, g2)
    if f_a == g_a:
        return f_b == g_b
    x = (f_b - g_b) / (f_a - g_a)
    return f1.x <= x <= f2.x and g1.x <= x <= g2.x

def line_collide_rect(f, g, a, b, c, d):
    # f, g -> line points
    # a, b, c, d -> rect points
    return line_collide(f, g, a, b) or \
           line_collide(f, g, b, c) or \
           line_collide(f, g, c, d) or \
           line_collide(f, g, a, d)

# Bresenham's algorithm 
# (https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm)
@convert_args_to_vectors
def line_npoints(f, g):
    if f == g:
        return [(f.x, f.y)]
    if f.x == g.x:
        if f.y > g.y: f, g = g, f
        return [(f.x, y) for y in range(math.floor(f.y), math.ceil(g.y))]
    steep = abs(g.y - f.y) > abs(g.x - f.x)
    if steep:
        f.x, f.y = f.y, f.x; g.x, g.y = g.y, g.x
    if f.x > g.x: 
        f, g = g, f
    deltax = g.x - f.x; deltay = abs(g.y - f.y)
    error = deltax // 2; ystep = 1 if f.y < g.y else -1
    y = f.y
    result = []
    for x in range(math.floor(f.x), math.ceil(g.x + 1)):
        result.append((y, x) if steep else (x, y))
        error -= deltay
        if error < 0:
            y += ystep; error += deltax
    return result

def rect_npoints(points):
    # TODO: use instead of pathfinding.get_path_npoints temporary solution
    ...

# Curves

def translate_to_zero_to_one_bounds(v, bounds):
    return ((v - bounds[0]) / (bounds[1] - bounds[0]))

# Bezier curve
# https://en.wikipedia.org/wiki/B%C3%A9zier_curve#Specific_cases
def bezier(*points: Vector):
    points = tuple(Vector(*p) for p in points)
    p = points # short-hand for the formulas below
    if len(points) == 2:    # Linear
        def b(t):
            return p[0] + t * (p[1] - p[0])
        return b
    elif len(points) == 3:  # Quadratic
        def b(t):
            a = (1 - t) * ((1 - t) * p[0] + t * p[1])
            b = t * ((1 - t) * p[1] + t * p[2])
            return a + b
        return b
    elif len(points) == 4:  # Cubic
        b012, b123 = bezier(points[0:3]), bezier(points[1:4])
        def b(t):
            return (1 - t) * b012(t) + t * b123(t)
    else:
        raise ValueError("Invalid number of points (from 2 to 4)")

class BezierDrawer:
    hostile = friendly = False
    def __init__(self, points, segments=40):
        self.points = points
        self.curve = bezier(*points)
        self.drawn_points = []
        for i in range(segments):
            pv = self.curve(i / segments)
            self.drawn_points.append(pv.as_list())
        print(self.drawn_points)

    def update(self):
        pass

    def draw(self, screen, pos_fix=(0, 0)):
        ps = [(p[0] + pos_fix[0], p[1] + pos_fix[1]) for p in self.drawn_points]
        pygame.draw.lines(screen, (255, 0, 0), False, ps, 2)
        for p in self.points:
            pygame.draw.circle(screen, (255, 0, 0), (int(p[0] + pos_fix[0]), int(p[1] + pos_fix[1])), 5)

def break_segment(p1, p2, angle, point=0.5):
    # For a given segment from point p1 to point p2,
    # return a the two and a third point p,
    # with the distance to each of the points equal to each other
    # the segment p-p1 forms the /angle/ with the segment p1-p2
    dv = Vector.from_points(p2, p1)
    new_angle = (dv.to_angle() + angle) % 360
    hypot = (1 / math.cos(math.radians(angle))) * dv.magnitude * point
    v = Vector.from_angle(new_angle) * hypot
    p = (p1[0] + v.x, p1[1] + v.y)
    return p1, p, p2

# Pygame utilities

def get_pygame_mouse_pos_rect():
    return pygame.Rect(pygame.mouse.get_pos(), (1, 1))

def norm_vector_to_mouse(f, fix=(0, 0)):
    m = get_pygame_mouse_pos_rect().move(fix)
    return Vector(m.x - f[0], m.y - f[1]).normalize()


class Register(dict):
    """
    Simple utility dict sub-class,
    used to automatically create registers of, for example:
    * enemies (e.g. for dynamic spawning in level)
    * spells (e.g. for the spell tree creation)
    Can be replaced with a simple dict named "register"
    in the respective modules.
    Used by saving,
    with the {"register_name": ..., "name": ...} save file construct

    Game modifications should add their classes to the registers.

    An alternative would be using IDs for every type and
    having a special function that would return a type for
    the given ID.
    This solution is only better in the fact it is created
    automatically.
    """
    registers = {}
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stype = None

    def __repr__(self):
        return "Register({})".format(dict(self))

    def __str__(self):
        return repr(self)

    @classmethod
    def gather_type(cls, stype, namespace, subclass=True, without_stype=True, ref_register=True):
        seq = []
        for obj in namespace.values():
            if without_stype and obj is stype:
                continue
            otype = obj if isinstance(obj, type) else type(obj)
            if isinstance(obj, stype) or (subclass and issubclass(otype, stype)):
                seq.append(obj)
        self = cls.from_sequence(seq, stype.__name__, ref_register)
        self.stype = stype
        return self

    @classmethod
    def from_sequence(cls, sequence, regname, ref_register=True):
        self = cls()
        cls.registers[regname] = self
        for obj in sequence:
            name = obj.__name__
            self[name] = obj
            if ref_register:
                obj.in_register = self
                obj.in_register_name = regname
        return self