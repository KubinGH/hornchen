import platform
import traceback

import pygame

import json_ext as json
from colors import Color
import controls
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
                # Try to evaluate (as an expression)
                result = eval(code, namespace, self.own_namespace)
            except SyntaxError:
                # Try to execute is as a statement
                try:
                    exec(code, namespace, self.own_namespace)
                    return ""
                except Exception as e:
                    return "[ERROR]" + traceback.format_exc()
            else:
                return str(result)
        except BaseException as e:
            # The evaluation/execution raised an exception
            if isinstance(e, SystemExit):
                raise
            else:
                return "[ERROR]" + traceback.format_exc()
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
    font_filename = "fonts/camingocode.ttf"
    font_size = 14
    font = fontutils.get_font(font_filename, font_size)
    valid_letter_range = range(pygame.K_a, pygame.K_z + 1)
    valid_chars = set(range(pygame.K_0, pygame.K_9 + 1)) | set(valid_letter_range) | \
                  {pygame.K_ASTERISK, pygame.K_COMMA, pygame.K_PERIOD, pygame.K_EQUALS,
                   pygame.K_GREATER, pygame.K_LESS, pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET,
                   pygame.K_LEFTPAREN, pygame.K_RIGHTPAREN, pygame.K_QUESTION, 
                   pygame.K_SEMICOLON, pygame.K_COLON, pygame.K_PLUS, pygame.K_MINUS, 
                   pygame.K_UNDERSCORE, pygame.K_SPACE, pygame.K_QUOTE, pygame.K_QUOTEDBL,
                   pygame.K_SLASH, pygame.K_BACKSLASH, pygame.K_DOLLAR, pygame.K_BACKQUOTE}
    shift_fixes = {
        pygame.K_1:         pygame.K_EXCLAIM,
        pygame.K_2:         pygame.K_AT,
        pygame.K_3:         pygame.K_HASH,
        pygame.K_4:         pygame.K_DOLLAR,
        pygame.K_5:         37, # percent sign
        pygame.K_6:         pygame.K_CARET,
        pygame.K_7:         pygame.K_AMPERSAND,
        pygame.K_8:         pygame.K_ASTERISK,
        pygame.K_9:         pygame.K_LEFTPAREN,
        pygame.K_0:         pygame.K_RIGHTPAREN,
        pygame.K_EQUALS:    pygame.K_PLUS,
        pygame.K_SEMICOLON: pygame.K_COLON,
        pygame.K_QUOTE:     pygame.K_QUOTEDBL,
        pygame.K_MINUS:     pygame.K_UNDERSCORE,
        pygame.K_LEFTBRACKET: 123,  # left curly bracket
        pygame.K_RIGHTBRACKET: 125, # right curly bracket,
        pygame.K_COMMA:     pygame.K_LESS,
        pygame.K_PERIOD:    pygame.K_GREATER,
        pygame.K_SLASH:     pygame.K_QUESTION,
        pygame.K_BACKSLASH: 124, # pipe character
        pygame.K_BACKQUOTE: 126, # tilde
    }
    uppercase_fix = -32 # a (97) -> A (65) when shift is pressed
    linegap = 1
    history_length_limit = 100
    current_line_prefix = ">>> "
    view_change_speed = 3
    # This won't work well with non-monospace fonts
    charsize = font.size(" ")
    charlimit = size[0] // charsize[0]
    def __init__(self, parent):
        self.parent = parent
        self.interpreter = EmbeddedInterpreter()
        self.background = self.get_empty_background_surface()
        self.rect = pygame.Rect((0, 0), self.size)
        self.renders = []
        self.view = 0
        self.current_line = ""
        self.history = []
        self.history_pointer = None
        self.pointer = None
        self.last_key = None
        self.last_char_pressed_for = 0
        self.next_last_char_cd = -1
        self.erase_all()
        inrend = fontutils.get_text_render(self.font, self.get_intext(), 
                                           False, Color.Green, None, False, False)
        self.add_to_output(inrend)

    def update(self, events, pressed_keys, mouse_pos, namespace=None):
        self.changed = False
        interpret_status = False
        edited_events = []
        shift = shift_pressed(pressed_keys)
        if self.last_key is not None and pressed_keys[self.last_key] and \
          not any(event.type == pygame.KEYDOWN for event in events):
            self.last_char_pressed_for += 1
        else:
            self.last_char_pressed_for = 0
        if self.last_char_pressed_for >= 40 and self.next_last_char_cd <= -1:
            self.next_last_char_cd = 3
        if not self.next_last_char_cd:
            events.append(pygame.event.Event(pygame.KEYDOWN, key=self.last_key))
        if self.next_last_char_cd >= 0:
            self.next_last_char_cd -= 1
        if pressed_keys[controls.ConsoleKeys.ScrollUp]:
            self.view -= self.view_change_speed
            if self.view < 0:
                self.view = 0
        if pressed_keys[controls.ConsoleKeys.ScrollDown]:
            self.view += self.view_change_speed
            lasty = self.renders[-1][1][1] + self.renders[-1][0].get_height()
            if self.view > lasty:
                self.view = lasty
        for event in events:
            mute = False
            if event.type == pygame.KEYDOWN:
                mute = True
                key = event.key
                if key != self.last_key:
                    self.last_char_pressed_for = 0
                self.last_key = key
                if event.key in self.valid_chars:
                    self.put_char(self.convert_key_to_char(key, shift))
                elif event.key == controls.ConsoleKeys.DeleteChar:
                    self.delete_char()
                elif event.key == controls.ConsoleKeys.Enter:
                    self.changed = True
                    if namespace is not None:
                        self.interpret_current(namespace)
                    else:
                        interpret_status = True
                elif event.key == controls.ConsoleKeys.DeleteLine:
                    if not shift:
                        self.erase_current()
                    else:
                        self.erase_all()
                elif event.key == controls.ConsoleKeys.HistoryNext:
                    if self.history:
                        if self.history_pointer is None:
                            self.history_pointer = 1
                        elif self.history_pointer < len(self.history):
                            self.history_pointer += 1
                        self.pointer = None
                        print(self.history_pointer, self.history[-self.history_pointer])
                        self.current_line = self.history[-self.history_pointer]
                        self.re_render_current()
                elif event.key == controls.ConsoleKeys.HistoryPrevious:
                    if self.history:
                        if self.history_pointer is None:
                            self.history_pointer = 1
                        elif self.history_pointer > 1:
                            self.history_pointer -= 1
                        self.pointer = None
                        print(self.history_pointer, self.history[-self.history_pointer])
                        self.current_line = self.history[-self.history_pointer]
                        self.re_render_current()
                elif event.key == controls.ConsoleKeys.PointerLeft:
                    if self.current_line and self.pointer is None:
                        self.pointer = -1
                    else:
                        if self.pointer > -len(self.current_line):
                            self.pointer -= 1
                    self.re_render_current()
                elif event.key == controls.ConsoleKeys.PointerRight:
                    if self.pointer is not None and self.pointer < -1:
                        self.pointer += 1
                    else:
                        self.pointer = None
                    self.re_render_current()
                else:
                    mute = False
            if not mute:
                edited_events.append(event)
                try:
                    pressed_keys[event.key] = 0
                except (IndexError, AttributeError):
                    pass
        events.clear(); events.extend(edited_events)
        for k in self.valid_chars | {pygame.K_BACKSPACE, pygame.K_RETURN, pygame.K_DELETE,
                                     pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
                                     pygame.K_PAGEUP, pygame.K_PAGEDOWN}:
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
        checkrect = pygame.Rect(-self.size[0], -self.size[1], self.size[0] * 2, self.size[1] * 2)
        for render, pos in self.renders + [(self.current_line_render, self.current_line_pos)]:
            apos = (pos[0], pos[1] - self.view)
            if self.rect.y - render.get_height() <= apos[1] <= self.rect.y + self.size[1]:
                area = render.get_rect().move(apos).clip(checkrect).move(-apos[0], -apos[1])
                screen.blit(render, apos, area)


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

    def get_intext(self):
        return "Python {} on {} {} [{}]".format(platform.python_branch(), platform.system(), platform.release(), platform.machine())

    def add_to_output(self, render):
        if render.get_height() < self.rect.height:
            self.renders.append((render, self.current_line_pos.copy()))
            self.current_line_pos[1] += render.get_height() + self.linegap
        else:
            parts = [render.subsurface(0, y, render.get_width(), min(render.get_height() - y, self.rect.height))
                     for y in range(0, render.get_height(), self.rect.height)]
            for part in parts:
                self.renders.append((part, self.current_line_pos.copy()))
                self.current_line_pos[1] += part.get_height()

    def re_render_current(self, with_vline=True):
        if with_vline and self.pointer is not None:
            i = self.pointer
            line = self.current_line[:i] + fontutils.VLINE + self.current_line[i:]
        else:
            line = self.current_line
        render = fontutils.get_text_render(self.font, self.current_line_prefix + line, 
                                           False, Color.White, None, False, False)
        self.current_line_render = render
        self.changed = True
        cbottom = self.current_line_pos[1] + self.current_line_render.get_height()
        if cbottom - self.view > self.rect.height:
            self.view = cbottom - self.rect.height

    def erase_current(self):
        if self.current_line and (not self.history or self.history[-1] != self.current_line):
            self.history.append(self.current_line)
            while len(self.history) > self.history_length_limit:
                self.history.pop(0)
        self.history_pointer = None
        self.pointer = None
        self.current_line = ""
        self.current_line_render = pygame.Surface((0, 0))
        self.re_render_current()

    def erase_all(self):
        self.current_line_pos = [0, 0]
        self.renders.clear()
        self.erase_current()

    def interpret_current(self, namespace):
        self.re_render_current(with_vline=False)
        self.add_to_output(self.current_line_render)
        interpret_line = fontutils.remove_render_tags_from_text(self.current_line)
        log("Interpreting: {}".format(interpret_line))
        result = self.interpreter.run(interpret_line, namespace)
        if result:
            log("Result:\n{}".format(result))
        if result and result != "None":
            try:
                color = Color.White
                if "[ERROR]" in result:
                    color = Color.Red
                    result = result.replace("[ERROR]", "")
                render = fontutils.get_multiline_text_render(self.font, result, False, color, 
                                                             None, self.linegap, dolog=False, cache=False, 
                                                             with_render_tags=False, wordwrap_chars=self.charlimit)
            except pygame.error as e:
                render = fontutils.get_text_render(self.font, "[Error while rendering output! '{}']".format(str(e)),
                                                   False, Color.Red, None, False, False)
            self.add_to_output(render)
            self.changed = True
        else:
            render = None
            log("No result")
        self.erase_current()

    def convert_key_to_char(self, key, shift):                   
        if shift:
            if key in self.valid_letter_range:
                key += self.uppercase_fix
            elif key in self.shift_fixes:
                key = self.shift_fixes[key]
        return chr(key)


    def put_char(self, char):
        if self.pointer is None:
            self.current_line += char
        else:
            i = self.pointer
            self.current_line = self.current_line[:i] + char + self.current_line[i:]
        self.re_render_current()

    def delete_char(self):
        if self.current_line:
            if self.pointer is None:
                self.current_line = self.current_line[:-1]
            else:
                i = self.pointer
                self.current_line = self.current_line[:i-1] + self.current_line[i:]
            self.re_render_current()