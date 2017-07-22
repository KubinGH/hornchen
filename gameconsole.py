from code import InteractiveInterpreter

import pygame

import json_ext as json
from colors import Color
import fontutils

print("Load game console")

def log(*args, **kwargs):
    args = ("[gameconsole]::" + str(args[0]), ) + args[1:]
    return print(*args, **kwargs)

class EmbeddedInterpreter:
    def __init__(self):
        self.own_namespace = {}

    def run(self, code, namespace):
        namespace.update(self.own_namespace)
        try:
            try:
                result = eval(code, namespace)
            except SyntaxError:
                try:
                    exec(code, namespace)
                    return ""
                except Exception as e:
                    return "[ERROR]{}: {}".format(type(e).__name__, str(e))
            else:
                return str(result)
        except BaseException as e:
            if isinstance(e, SystemExit):
                raise
            else:
                return "[ERROR]{}: {}".format(type(e).__name__, str(e))
        return ""

def shift_pressed(pressed_keys):
    return pressed_keys[pygame.K_LSHIFT] or pressed_keys[pygame.K_RSHIFT]


class GameConsole:
    class Status:
        Standby = 0
        Interpret = 1
    config = json.loadf("configs/console.json")
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
                   pygame.K_SLASH, pygame.K_BACKSLASH, pygame.K_DOLLAR}
    shift_fixes = {
        pygame.K_4:         pygame.K_DOLLAR,
        pygame.K_8:         pygame.K_ASTERISK,
        pygame.K_9:         pygame.K_LEFTPAREN,
        pygame.K_0:         pygame.K_RIGHTPAREN,
        pygame.K_EQUALS:    pygame.K_PLUS,
        pygame.K_SEMICOLON: pygame.K_COLON,
        pygame.K_QUOTE:     pygame.K_QUOTEDBL,
        pygame.K_MINUS:     pygame.K_UNDERSCORE,
        pygame.K_LEFTBRACKET: 123,  # left curly bracket
        pygame.K_RIGHTBRACKET: 125, # right curly bracket
    }
    uppercase_fix = -32 # a (97) -> A (65) when shift is pressed
    linegap = 1
    current_line_prefix = "> "
    def __init__(self, parent):
        self.parent = parent
        self.interpreter = EmbeddedInterpreter()
        self.background = self.get_empty_background_surface()
        self.output = self.get_empty_output_surface()
        self.rect = self.output.get_rect()
        self.rect.x, self.rect.y = 0, 0
        self.current_line = None
        self.last_line = None
        self.erase_all()

    def update(self, events, pressed_keys, mouse_pos, namespace=None):
        self.changed = False
        interpret_status = False
        edited_events = []
        shift = shift_pressed(pressed_keys)
        for event in events:
            mute = False
            if event.type == pygame.KEYDOWN:
                mute = True
                if event.key in self.valid_chars:
                    key = event.key
                    if shift:
                        if key in self.valid_letter_range:
                            key += self.uppercase_fix
                        elif key in self.shift_fixes:
                            key = self.shift_fixes[key]
                    keych = chr(key)
                    self.current_line += keych
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
                    self.changed = True
                    if namespace is not None:
                        self.interpret_current(namespace)
                    else:
                        interpret_status = True
                elif event.key == pygame.K_HOME:
                    if self.last_line is not None:
                        self.current_line = self.last_line
                        self.last_line = None
                        self.re_render_current()
                else:
                    mute = False
            if not mute:
                edited_events.append(event)
        events.clear(); events.extend(edited_events)
        for k in self.valid_chars:
            try:
                pressed_keys[k] = 0
            except IndexError:
                pass
        if interpret_status:
            return self.Status.Interpret
        else:
            return self.Status.Standby

    def draw(self, screen):
        screen.blit(self.background, self.rect)
        screen.blit(self.output, self.rect)
        screen.blit(self.current_line_render, self.current_line_pos)
        if self.changed:
            return self.rect

    def get_empty_background_surface(self):
        surface = pygame.Surface(self.size)
        surface.fill(self.background_color[:3])
        surface.set_alpha(self.background_color[3])
        return surface

    def get_empty_output_surface(self):
        surface = pygame.Surface(self.size)
        surface.fill(Color.Black)
        surface.set_colorkey(Color.Black)
        return surface

    def re_render_current(self):
        rend = fontutils.get_text_render(self.font, self.current_line_prefix + self.current_line, 
                                         False, Color.White, None, False)
        self.current_line_render = rend
        return rend

    def erase_current(self):
        self.last_line = self.current_line
        self.current_line = ""
        self.current_line_render = pygame.Surface((0, 0))
        self.re_render_current()

    def erase_all(self):
        self.output = self.get_empty_output_surface()
        self.current_line_pos = [0, 0]
        self.erase_current()

    def interpret_current(self, namespace):
        log("Interpreting: {}".format(self.current_line))
        result = self.interpreter.run(self.current_line, namespace)
        self.output.blit(self.current_line_render, self.current_line_pos)
        self.current_line_pos[1] += self.current_line_render.get_height() + self.linegap
        if result:
            log("Result:\n {}".format(result))
            try:
                color = Color.White
                if result.startswith("[ERROR]"):
                    color = Color.Red
                    result = result[7:]
                rend = fontutils.get_multiline_text_render(self.font, result, False, color, 
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