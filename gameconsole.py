from code import InteractiveInterpreter

import pygame

import json_ext as json
from colors import Color
import fontutils

def log(*args, **kwargs):
    args = ("[gameconsole]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

class EmbeddedConsole:
    def __init__(self):
        self.own_namespace = {}

    def run(self, code, namespace):
        try:
            result = eval(code, namespace, self.own_namespace)
            return str(result)
        except BaseException as e:
            if isinstance(e, SystemExit):
                raise
            else:
                return "{}: {}".format(type(e).__name__, str(e))

def shift_pressed(pressed_keys):
    return pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]

class GameConsole:
    config = json.load(open("configs/console.json", "r"))
    size = config["console_size"]
    background_color = config["console_background_color"]
    font = fontutils.get_font("fonts/camingocode.ttf", 16)
    valid_letter_range = range(pygame.K_a, pygame.K_z + 1)
    valid_chars = set(range(pygame.K_0, pygame.K_9 + 1)) | set(valid_letter_range) | \
                  {pygame.K_ASTERISK, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_EQUALS,
                   pygame.K_GREATER, pygame.K_LESS, pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET,
                   pygame.K_LEFTPAREN, pygame.K_RIGHTPAREN, pygame.K_QUESTION, 
                   pygame.K_SEMICOLON, pygame.K_COLON, pygame.K_PLUS, pygame.K_MINUS, 
                   pygame.K_UNDERSCORE, pygame.K_SPACE, pygame.K_QUOTE, pygame.K_QUOTEDBL,
                   pygame.K_SLASH, pygame.K_BACKSLASH}
    shift_fixes = {
        pygame.K_8:         pygame.K_ASTERISK,
        pygame.K_EQUALS:    pygame.K_PLUS,
        pygame.K_9:         pygame.K_LEFTPAREN,
        pygame.K_0:         pygame.K_RIGHTPAREN,
        pygame.K_SEMICOLON: pygame.K_COLON,
        pygame.K_QUOTE:     pygame.K_QUOTEDBL,
        pygame.K_MINUS:     pygame.K_UNDERSCORE,
        pygame.K_LEFTBRACKET: 123,
        pygame.K_RIGHTBRACKET: 125,
    }
    uppercase_fix = -32
    linegap = 1
    current_line_prefix = "> "
    def __init__(self, parent):
        self.parent = parent
        self.console = EmbeddedConsole()
        self.console_background = pygame.Surface(self.size).convert_alpha()
        self.console_background.fill(self.background_color)
        self.rect = self.console_background.get_rect()
        self.rect.x, self.rect.y = 0, 0
        self.output =  pygame.Surface(self.size)
        self.output.fill(Color.Black)
        self.output.set_colorkey(Color.Black)
        self.erase_all()

    def update(self, mouse_pos, pressed_keys, events, namespace):
        self.changed = False
        shift = shift_pressed(pressed_keys)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in self.valid_chars:
                    key = event.key
                    if shift:
                        if key in self.valid_letter_range:
                            key += self.uppercase_fix
                        elif key in self.shift_fixes:
                            key = self.shift_fixes[key]
                    key = chr(key)
                    self.current_line += key
                    self.re_render_current()
                    self.changed = True
                elif event.key == pygame.K_BACKSPACE:
                    if shift:
                        self.erase_all()
                    elif self.current_line:
                        self.current_line = self.current_line[:-1]
                        self.re_render_current()
                    self.changed = True
                elif event.key == pygame.K_RETURN:
                    self.interpret_current(namespace)
                    self.changed = True

    def draw(self, screen):
        screen.blit(self.console_background, self.rect)
        screen.blit(self.output, self.rect)
        screen.blit(self.current_line_render, self.current_line_pos)
        if self.changed:
            return self.rect

    def re_render_current(self):
        rend = fontutils.get_text_render(self.font, self.current_line_prefix + self.current_line, 
                                         False, Color.White, None, False)
        self.current_line_render = rend
        return rend

    def erase_current(self):
        self.current_line = ""
        self.current_line_render = pygame.Surface((0, 0))
        self.re_render_current()

    def erase_all(self):
        self.output.fill(Color.Black)
        self.current_line_pos = [0, 0]
        self.erase_current()

    def interpret_current(self, namespace):
        log("Interpreting: {}".format(self.current_line))
        result = self.console.run(self.current_line, namespace)
        self.output.blit(self.current_line_render, self.current_line_pos)
        self.current_line_pos[1] += self.current_line_render.get_height() + self.linegap
        if result:
            log("Result:\n {}".format(result))
            try:
                rend = fontutils.get_multiline_text_render(self.font, result, False, Color.White, 
                                                           None, self.linegap, False)
            except pygame.error as e:
                rend = fontutils.get_text_render(self.font, "[Error while rendering output! '{}']".format(str(e)),
                                                 False, Color.Red, None, False)
            self.output.blit(rend, self.current_line_pos)
            self.current_line_pos[1] += rend.get_height() + self.linegap
        else:
            log("No result")
        if self.current_line_pos[1] > self.rect.height - self.linegap:
            self.erase_all()
        else:
            self.erase_current()