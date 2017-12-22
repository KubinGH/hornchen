print("Load color")

class Color:
    Black =     (  0,   0,   0)
    White =     (255, 255, 255)

    lGray =     (215, 215, 215)
    Gray =      (170, 170, 170)
    dGray =     (115, 115, 115)

    Red =       (255,   0,   0)
    Green =     (  0, 255,   0)
    Blue =      (  0,   0, 255)

    Yellow =    (255, 255,   0)
    Cyan =      (  0, 255, 255)
    Purple2 =    (255,   0, 255)

    Magenta =   (255,   0, 144)
    Pink =      (255,  51,  80)
    Purple =    (180,   0, 180)

    lBlue =     (100, 100, 255)
    dBlue =     (  0,   0, 125)
    eBlue =     (  0,   0, 100)

    lPink =     (255, 200, 240)
    Orange =    (255, 150,   0)

    colors = ["Black", "White",
              "lGray", "Gray", "dGray",
              "Red", "Green", "Blue",
              "Yellow", "Cyan", "Purple2",
              "Magenta", "Pink", "Purple",
              "lBlue", "dBlue", "eBlue",
              "lPink", "Orange"]
    
    @staticmethod
    def with_alpha(alpha):
        return _ColorWithAlpha(alpha)

    @classmethod
    def by_name(cls, name):
        if name not in cls.colors:
            return cls.White
        return getattr(cls, name)

_DUMMY = Color()

class _ColorWithAlpha:
    def __init__(self, alpha):
        self.alpha = alpha
    
    def __getattr__(self, name):
        return _DUMMY.by_name(name) + (self.alpha, )
        
def invert_color(color):
    return tuple(255 - c for c in color)