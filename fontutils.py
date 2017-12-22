import re
import warnings
import zipopen
import pygame
from colors import Color

class NamedFont(pygame.font.Font):
    def __init__(self, *args, name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    def __repr__(self):
        return "<Font: '{}'>".format(self.name)

if zipopen.enable_resource_zip:
    def load_font(source, size):
        return NamedFont(zipopen.open(source, "rb"), size, name=str(source))
else:    
    def load_font(source, size):
        return NamedFont(source, size, name=str(source))

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
VLINE = "[VERTICAL_LINE]"
COLOR_MARK = "\[COLOR:([a-zA-Z]+)\]"
last_color_mark = None
def get_text_render(font, text, antialias, color, background=None, dolog=True, cache=True, with_render_tags=True):
    global last_color_mark
    params = (font, text, antialias, color, background)
    if params not in render_cache:
        if dolog: log("Text render: {}".format(params))
        # Render tags code, supports:
        # * changing color with [COLOR:<name>] syntax, where <name> is a valid colors.Color attribute name
        # * drawing vertical lines in the middle of the text
        last_color_mark = None
        color_marks = list(re.finditer(COLOR_MARK, text))
        if with_render_tags and color_marks:
            get = lambda text, color: get_text_render(font, text, antialias, color, background, False, False)
            renders = []
            last_span = (0, 0)
            if color_marks[0].span()[0] > 0:
                renders.append(get(text[:color_marks[0].span()[0]], color))
                last_span = (0, color_marks[0].span()[0])
            for mark1, mark2 in zip(color_marks[:-1], color_marks[1:]):
                span1, span2 = mark1.span(), mark2.span()
                renders.append(get(text[span1[1]:span2[0]], Color.by_name(mark1.group(1))))
                last_span = span1
            last_mark = color_marks[-1]
            last_color_mark = Color.by_name(last_mark.group(1))
            renders.append(get(text[last_mark.span()[1]:], last_color_mark))
            last_color_mark = Color.by_name(last_mark.group(1))
            size = (sum(r.get_width() for r in renders), max(r.get_height() for r in renders))
            surface = pygame.Surface(size, pygame.SRCALPHA).convert_alpha()
            pos = [0, 0]
            for r in renders:
                surface.blit(r, pos)
                pos[0] += r.get_width()
        elif with_render_tags and VLINE in text:
            line_indexes = []
            for i, ch in enumerate(text[:-len(VLINE)+1]):
                if ch == "[" and text[i:i+len(VLINE)] == VLINE:
                    line_indexes.append(i - len(VLINE) * len(line_indexes))
            text = text.replace(VLINE, "")
            surface = font.render(text, antialias, color, background).convert_alpha()
            for x, i in enumerate(line_indexes):
                point = list(font.size(text[:i]))
                if x == len(line_indexes) - 1:
                    point[0] -= 1
                elif x > 0 and line_indexes[x - 1] == i - len(VLINE):
                    point[0] += 1
                pygame.draw.line(surface, color, (point[0], 0), point)
        else:
            surface = font.render(text, antialias, color, background).convert_alpha()
        if not cache:
            return surface
        render_cache[params] = surface
    return render_cache[params]

multiline_render_cache = {}
def get_multiline_text_render(font, text, antialias, color, background=None, linegap=2, dolog=False, cache=True, with_render_tags=True, wordwrap_chars=None):
    global last_color_mark
    params = (font, text, antialias, color, background, linegap)
    if params not in multiline_render_cache:
        text = text.strip()
        # Word wrapping
        if wordwrap_chars is not None:
            lines = text.split("\n")
            for i in range(len(lines)):
                text_w = ""
                lim = wordwrap_chars
                left = lim
                line = ""
                for word in lines[i].split(" "):
                    if len(word) + 1 > left:
                        left = lim - len(word)
                        for i in range(lim, len(line), lim):
                            line = line[:i].rstrip() + "\n" + line[i:].lstrip()
                        line = line.strip()
                        text_w += line + "\n"
                        line = ""
                    else:
                        left -= len(word) + 1
                    line += word + " "
                if line:
                    for i in range(lim, len(line), lim):
                        line = line[:i].rstrip() + "\n" + line[i:].lstrip()
                    line = line.strip()
                text_w += line
                lines[i] = text_w
            text = "\n".join(lines)
        last_color_mark = None
        lines_render = []
        for line in text.split("\n"):
            if with_render_tags and last_color_mark != None:
                color = last_color_mark
            r = get_text_render(font, line, antialias, last_color_mark or color, background, dolog, cache, with_render_tags)
            lines_render.append(r)
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
        if not cache:
            return surface
        multiline_render_cache[params] = surface
    return multiline_render_cache[params]

def remove_render_tags_from_text(text):
    text = text.replace(VLINE, "")
    text = re.sub(COLOR_MARK, "", text)
    return text