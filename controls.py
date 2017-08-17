#TODO: Base on keydown events and keyboard.get_pressed
#      create a configurable controls system

import pygame

class Key:
    def __init__(self, *args):
        self.values = args

    def __eq__(self, other):
        return other in self.values

    def __contains__(self, other):
        return self == other

class KeyboardState:
    def __init__(self, pressed_keys):
        self.pressed_keys = pressed_keys

    def __getitem__(self, key):
        if isinstance(key, Key):
            return any(self.pressed_keys[v] for v in key.values)
        else:
            return self.pressed_keys[key]



class Keys:
    Left = Key(pygame.K_LEFT, pygame.K_a)
    Right = Key(pygame.K_RIGHT, pygame.K_d)
    Up = Key(pygame.K_UP, pygame.K_w)
    Down = Key(pygame.K_DOWN, pygame.K_s)

    Action1 = Key(pygame.K_z)
    Action2 = Key(pygame.K_x)
    Action3 = Key(pygame.K_SPACE)

    Sprint = Key(pygame.K_v)
    Crouch = Key(pygame.K_c)