import warnings
import zipopen
import pygame
from colors import Color

load_font = pygame.font.Font

if zipopen.enable_resource_zip:
    def load_font(source, size):
        return pygame.font.Font(zipopen.open(source, "rb"), size)

print("Load font utilities")

def log(*args, **kwargs):
    args = ("[fontutils]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

def color_as_tuple(pgcolor):
    return (pgcolor.r, pgcolor.g, pgcolor.b, pgcolor.a)

font_cache = {}
def get_font(source, size, ignore_missing=True):
    pair = (source, size)
    if pair not in font_cache:
        log("Load font:", pair)
        try:
            font_cache[pair] = load_font(source, size)
        except OSError:
            if ignore_missing:
                return pygame.font.SysFont("monospace", size)
            else:
                raise
    return font_cache[pair]

def get_sysfont(source, size, bold=False, italic=False):
    params = (source, size, bold, italic)
    if params not in font_cache:
        log("Load sys font:", params)
        font_cache[params] = pygame.font.SysFont(source, size, bold, italic)
    return font_cache[params]


render_cache = {}
def get_text_render(font, text, antialias, color, background=None, dolog=True):
    params = (font, text, antialias, color, background)
    if params not in render_cache:
        if dolog: log("Text render: {}".format(params))
        render_cache[params] = font.render(text, antialias, color, background).convert_alpha()
    return render_cache[params]

multiline_render_cache = {}
def get_multiline_text_render(font, text, antialias, color, background=None, linegap=2, dolog=False):
    params = (font, text, antialias, color, background, linegap)
    if params not in multiline_render_cache:
        lines_render = [get_text_render(font, line, antialias, color, background, dolog)
                        for line in text.strip().split("\n")]
        width = max(surface.get_width() for surface in lines_render)
        height = sum(surface.get_height() for surface in lines_render) + \
                    (linegap * (len(lines_render) - 1))
        surface = pygame.Surface((width, height))
        colorkey = Color.Black if color is not Color.Black else (0, 0, 1)
        surface.fill(colorkey)
        surface.set_colorkey(colorkey)
        current_height = 0
        for render in lines_render:
            surface.blit(render, (0, current_height))
            current_height += render.get_height() + linegap
        multiline_render_cache[params] = surface
    return multiline_render_cache[params]
