import functools
import warnings
import pygame
from colors import Color

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

loaded_images = {}
def load_image_from_file(filename, hint=None):
    if filename not in loaded_images:
        log("Load image:", filename)
        this = pygame.image.load(filename)
        try:
            this_copy = this.copy()
            pixelarr = pygame.PixelArray(this)
            pixelarr.replace(Color.White, (0, 0, 1), weights=(0, 0, 0))
            this = this.convert()
            this.set_colorkey(Color.White)
        except:
            pass
        else:
            this = this_copy
        loaded_images[filename] = this
    return loaded_images[filename]


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

cborders_cache = {}
def color_border(size, color, thickness):
    color = color_as_tuple(color)
    params = (size, color)
    if params not in cborders_cache:
        log("Create color border:", params)
        width, height = size
        surface = pygame.Surface(size)
        if color != Color.Black:
            colorkey = Color.Black
        else:
            colorkey = color.White
        surface.fill(colorkey)
        rects = [pygame.Rect(0, 0, width, thickness),
                 pygame.Rect(0, height-thickness, width, thickness),
                 pygame.Rect(0, 0, thickness, height),
                 pygame.Rect(width-thickness, 0, thickness, height)]
        [pygame.draw.rect(surface, color, rect) for rect in rects]
        surface.set_colorkey(colorkey)
        cborders_cache[params] = surface
    return cborders_cache[params]

iborders_cache = {}
def image_border(size, image):
    params = (size, image)
    if params not in iborders_cache:
        log("Create image border:", params)
        width, height = size
        image_size = image.get_size()
        image_width, image_height = image_size
        if width % image_width or height % image_height:
            warnings.warn("Image in border doesn't fit perfectly")
        surface = pygame.Surface(size)
        surface.fill((3, 14, 15))
        for x in range(0, width + 1, image_width):
            surface.blit(image, (x, 0))
            surface.blit(image, (x, height - image_height))
        for y in range(0, height + 1, image_height):
            surface.blit(image, (0, y))
            surface.blit(image, (width - image_width, y))
        surface.set_colorkey((3, 14, 15))
        iborders_cache[params] = surface
    return iborders_cache[params]

scale_cache = {}
def scale(surface, size):
    size = tuple(size)
    params = (surface, size)
    if params not in scale_cache:
        log("Scale image:", params)
        surface_size = surface.get_size()
        if size[0] // 2 == surface_size[0] and size[1] // 2 == surface_size[1]:
            scale_cache[params] = pygame.transform.scale2x(surface)
        else:
            scale_cache[params] = pygame.transform.scale(surface, size)
    return scale_cache[params]

def scale2x(surface):
    surface_size = surface.get_size()
    return scale(surface, (surface_size[0] * 2, surface_size[1] * 2))