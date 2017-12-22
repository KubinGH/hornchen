import math
import functools
import warnings, inspect # For outdated/unoptimal functions
import pygame
from colors import Color
from animation import Animation
import zipopen

image_load = pygame.image.load # Needed for zip hook

if zipopen.enable_resource_zip:
    def image_load(filename):
        return pygame.image.load(zipopen.open(filename, "rb"))

print("Load image library")

def log(*args, **kwargs):
    args = ("[imglib]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

def color_as_tuple(color):
    if isinstance(color, pygame.Color):
        return (color.r, color.g, color.b, color.a)
    elif isinstance(color, (list, tuple)):
        return tuple(color) if len(color) == 4 else tuple(color) + (255, )
    else:
        return color

def rgb_number_to_tuple(number):
    return (number >> 1) & 255, (number >> 8) & 255, (number >> 16) & 255

def get_missing_surface(size=(100, 100)):
    half = (int(size[0] / 2), int(size[1] / 2))
    surface = pygame.Surface(size)
    surface.fill(Color.Purple)
    surface.fill(Color.Black, pygame.Rect(0, 0, half[0], half[1]))
    surface.fill(Color.Black, pygame.Rect(half[0], half[1], half[0], half[1]))
    return surface

def simple_scale(surface, dwidth, dheight):
    source = pygame.PixelArray(surface)
    width, height = size = source.shape
    newsize = (width * dwidth, height * dheight)
    array = pygame.PixelArray(pygame.Surface(newsize).convert_alpha())
    for x in range(width):
        for y in range(height):
            value = source[x, y]
            ax, ay = x * dwidth, y * dheight
            array[ax:ax+dwidth, ay:ay+dheight] = value
    result = array.surface
    # Release the surfaces
    del source, array
    return result

scale_cache = {}
def scale(surface, size, smooth=False, *, docache=True, dolog=True):
    size = tuple(size)
    params = (surface, size)
    if params not in scale_cache:
        surface_size = surface.get_size()
        dw, dh = size[0] / surface_size[0], size[1] / surface_size[1]
        if dw == dh == 1:
            return surface
        if dolog:
            log("Scale image:", params)
        if not smooth and (dw % 1 == dh % 1 == 0):
            result = simple_scale(surface, int(dw), int(dh))
        elif dw == dh == 2:
            result = pygame.transform.scale2x(surface)
        elif dw == dh and dw % 1 == 0 and (int(dw) & (int(dw) - 1)) == 0: # scale is a power of 2
            result = scale(pygame.transform.scale2x(surface), size)
        else:
            result = pygame.transform.scale(surface, size)
        result = result.convert_alpha()
        if not docache:
            return result
        scale_cache[params] = result 
    return scale_cache[params]

def scale2x(surface):
    surface_size = surface.get_size()
    return scale(surface, (surface_size[0] * 2, surface_size[1] * 2))


loaded_images = {}
def load_image_from_file(filename, ignore_missing=False, *, docache=True, after_scale=None):
    if filename not in loaded_images:
        log("Load image:", filename)
        try:
            this = image_load(filename)
            this = this.convert_alpha()
        except pygame.error:
            if ignore_missing:
                this = get_missing_surface()
            else:
                raise
        if not docache:
            if after_scale is None:
                return this
            else:
                return scale(loaded_images[filename], after_scale, docache=docache)
        loaded_images[filename] = this
    if after_scale is None:
        return loaded_images[filename]
    else:
        return scale(loaded_images[filename], after_scale, docache=docache)

repeatimg_cache = {}
def repeated_image_texture(image, size):
    params = (image, size)
    if params not in repeatimg_cache:
        log("Create repeated image texture:", params)
        width, height = size
        imgwidth, imgheight = image.get_size()
        surface = pygame.Surface(size)
        for x in range(0, width + 1, imgwidth):
            for y in range(0, height + 1, imgheight):
                surface.blit(image, (x, y))
        repeatimg_cache[params] = surface
    return repeatimg_cache[params]


class ColorBorderDrawer:
    def __init__(self, size, color, thickness):
        self.size, self.color, self.thickness = size, color, thickness
        self.color = color_as_tuple(self.color)

    def draw(self, surface, pos=(0, 0)):
        width, height = self.size
        size, color, thickness = self.size, self.color, self.thickness
        rects = [pygame.Rect(pos[0], pos[1], width, thickness),
                 pygame.Rect(pos[0], pos[1] + height - thickness, width, thickness),
                 pygame.Rect(pos[0], pos[1], thickness, height),
                 pygame.Rect(pos[0] + width - thickness, pos[1], thickness, height)]
        for rect in rects:
            surface.fill(color, rect)
        return rects

cborders_cache = {}
def color_border(size, color, thickness, nowarn=False):
    if not nowarn:
        frame, filename, line_number, function_name, lines, index = inspect.stack()[1]
        warnings.warn("[O] color_border call from {}@line {}, use ColorBorderDrawer instead".format(filename, line_number))
    color = color_as_tuple(color)
    params = (size, color, thickness)
    if params not in cborders_cache:
        log("Create color border:", params)
        width, height = size
        surface = pygame.Surface(size)
        if color != Color.Black:
            colorkey = Color.Black
        else:
            colorkey = color.White
        surface.fill(colorkey)
        surface.set_colorkey(colorkey)
        drawer = ColorBorderDrawer(size, color, thickness)
        drawer.draw(surface)
        cborders_cache[params] = surface
    return cborders_cache[params]


class ImageBorderDrawer:
    def __init__(self, size, image):
        self.size, self.image = size, image

    def draw(self, screen, pos=(0, 0)):
        size, image = self.size, self.image
        width, height = size
        image_width, image_height = image.get_size()
        for x in range(0, width + 1, image_width):
            screen.blit(image, (pos[0] + x, pos[1]))
            screen.blit(image, (pos[0] + x, pos[1] + height - image_height))
        for y in range(0, height + 1, image_height):
            screen.blit(image, (pos[0], pos[1] + y))
            screen.blit(image, (pos[0] + width - image_width, pos[1] + y))

iborders_cache = {}
def image_border(size, image, nowarn=False):
    if not nowarn:
        frame, filename, line_number, function_name, lines, index = inspect.stack()[1]
        warnings.warn("[O] image_border call from {}@line {}, use ImageBorderDrawer instead".format(filename, line_number))
    params = (size, image)
    if params not in iborders_cache:
        log("Create image border:", params)
        width, height = size
        image_size = image.get_size()
        image_width, image_height = image_size
        if width % image_width or height % image_height:
            warnings.warn("Image in border doesn't fit perfectly")
        surface = pygame.Surface(size)
        drawer = ImageBorderDrawer(size, image)
        surface.fill((3, 14, 15)) # Who would use such a color?
        surface.set_colorkey((3, 14, 15))
        drawer.draw(surface)
        iborders_cache[params] = surface
    return iborders_cache[params]


loaded_animations_w = {}
def animation_w_from_file(filename, frame_width, tick):
    params = (filename, frame_width, tick)
    if params not in loaded_animations_w:
        image = load_image_from_file(filename)
        loaded_animations_w[params] = Animation.from_surface_w(image, frame_width, tick)
    return loaded_animations_w[params]

loaded_animations_h = {}
def animation_h_from_file(filename, frame_height, tick):
    params = (filename, frame_height, tick)
    if params not in loaded_animations_h:
        image = load_image_from_file(filename)
        loaded_animations_h[params] = Animation.from_surface_h(image, frame_height, tick)
    return loaded_animations_h[params]


class ValueRotationDependent:
    def __init__(self, right, left, up, down):
        self.right, self.left, self.up, self.down = right, left, up, down

    def __getitem__(self, key):
        return getattr(self, key)

    @property
    def as_list(self):
        return [self.right, self.left, self.up, self.down] 

def all_rotations(right):
    left = pygame.transform.flip(right, 1, 0) # surface, xbool, ybool
    down = pygame.transform.rotate(right, -90)
    up = pygame.transform.flip(down, 0, 1)
    return ValueRotationDependent(right, left, up, down)


dim_cache = {}
def dim_surface(surface, alpha, color=Color.Black):
    params = (surface, alpha)
    if params not in dim_cache:
        dimmer = pygame.Surface(surface.get_size()).convert_alpha()
        dimmer.fill(color + (alpha, ))
        result = surface.convert_alpha()
        result.blit(dimmer, (0, 0))
        dim_cache[params] = result
    return dim_cache[params]

# From a pygame tutorial, draws a proper outline... sometimes.
def draw_circle(surface, color, pos, radius, width=0, it=150):
    if width < 3:
        pygame.draw.circle(surface, color, pos, int(radius), int(width))
        return
    center_x, center_y = pos
    for i in range(it):
        ang = i * math.pi * 2 / it
        dx = int(math.cos(ang) * radius)
        dy = int(math.sin(ang) * radius)
        x = center_x + dx
        y = center_y + dy
        pygame.draw.circle(surface, color, (x, y), int(width))

in_circle_cache = {}
def in_circle(surface, border_width=0, border_color=Color.White):
    params = (surface, border_width, border_color)
    if params not in in_circle_cache:
        result = surface.convert_alpha()
        s = min(result.get_size())
        center = result.get_rect().center
        out = s * (1 - math.sqrt(2) / 2)
        draw_circle(result, (0, 0, 0, 0), center, s * math.sqrt(2) / 2 + out / 2 - s // 10, out)
        if border_width > 0:
            pygame.draw.circle(result, border_color, center, s // 2, border_width)
        in_circle_cache[params] = result
    return in_circle_cache[params]

rotate_cache = {}
def rotate(surface, angle):
    params = (surface, angle)
    if params not in rotate_cache:
        result = pygame.transform.rotate(surface, angle)
        rotate_cache[params] = result
    return rotate_cache[params]

tint_cache = {}
def tint(surface, color):
    params = (surface, color)
    if params not in tint_cache:
        result = surface.copy()
        result.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        tint_cache[params] = result
    return tint_cache[params]

def apply_alpha(surface, alpha):
    result = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    result.fill((255, 255, 255, alpha))
    result.blit(surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result