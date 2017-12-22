#TODO: Base on keydown events and keyboard.get_pressed
#      create a configurable controls system

import pygame
from enum import Enum

print("Load controls")

class Key:
    def __init__(self, *args):
        self.values = args

    def __eq__(self, other):
        return other in self.values
    def __contains__(self, other):
        return other in self.values

class KeyboardState:
    def __init__(self, pressed_keys):
        self.pressed_keys = list(pressed_keys)

    def __getitem__(self, key):
        if isinstance(key, Key):
            return any(self.pressed_keys[v] for v in key.values)
        else:
            return self.pressed_keys[key]

    def __setitem__(self, key, value):
        if isinstance(key, Key):
            for v in key.values:
                self.pressed_keys[v] = value
        else:
            self.pressed_keys[key] = value



class Keys:
    Left = Key(pygame.K_LEFT, pygame.K_a)
    Right = Key(pygame.K_RIGHT, pygame.K_d)
    Up = Key(pygame.K_UP, pygame.K_w)
    Down = Key(pygame.K_DOWN, pygame.K_s)

    UseItem = Key(pygame.K_z)
    CastSpell = Key(pygame.K_x)
    ActivateTile = Key(pygame.K_SPACE)

    Sprint = Key(pygame.K_v)
    Crouch = Key(pygame.K_c)

class MenuKeys:
    Left = Key(pygame.K_LEFT, pygame.K_a)
    Right = Key(pygame.K_RIGHT, pygame.K_d)
    Up = Key(pygame.K_UP, pygame.K_w)
    Down = Key(pygame.K_DOWN, pygame.K_s)

    Action1 = Key(pygame.K_z)
    Action2 = Key(pygame.K_x)
    Action3 = Key(pygame.K_SPACE)

    Pause = Key(pygame.K_ESCAPE)
    PlayerInventory = Key(pygame.K_i)
    MinimapView = Key(pygame.K_m)
    SpellTree = Key(pygame.K_t)

    MinimapView_MoveToPlayer = Key(pygame.K_p)

    Leave = Key(pygame.K_ESCAPE, pygame.K_RETURN)

class DebugKeys:
    ToggleConsole = Key(pygame.K_F2)
    ToggleDebug = Key(pygame.K_F3)
    ToggleMouse = Key(pygame.K_F6)
    ToggleFullscreen = Key(pygame.K_F11)
    TakeScreenshot = Key(pygame.K_F12)

class ConsoleKeys:
    Enter = Key(pygame.K_RETURN)
    DeleteChar = Key(pygame.K_BACKSPACE)
    DeleteLine = Key(pygame.K_DELETE)
    ScrollUp = Key(pygame.K_PAGEUP)
    ScrollDown = Key(pygame.K_PAGEDOWN)
    HistoryNext = Key(pygame.K_UP)
    HistoryPrevious = Key(pygame.K_DOWN)
    PointerLeft = Key(pygame.K_LEFT)
    PointerRight = Key(pygame.K_RIGHT)