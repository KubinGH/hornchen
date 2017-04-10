import pygame
import warnings

def log(*args, **kwargs):
    args = ("[fontutils]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

def color_as_tuple(pgcolor):
    return (pgcolor.r, pgcolor.g, pgcolor.b, pgcolor.a)

font_cache = {}
def get_font(source, size):
    pair = (source, size)
    if pair not in font_cache:
        log("Load font:", pair)
        font_cache[pair] = pygame.font.Font(source, size)
    return font_cache[pair]

def get_sysfont(source, size, bold=False, italic=False):
    params = (source, size, bold, italic)
    if params not in font_cache:
        log("Load sys font:", params)
        font_cache[params] = pygame.font.SysFont(source, size, bold, italic)
    return font_cache[params]


render_cache = {}
def get_text_render(font, text, antialias, color, background=None, dolog=True):
    if isinstance(color, pygame.Color):
        color = color_as_tuple(color)
    params = (font, text, antialias, color, background)
    if params not in render_cache:
        if dolog: log("Text render: {}".format(params))
        render_cache[params] = font.render(text, antialias, color, background)
    return render_cache[params]