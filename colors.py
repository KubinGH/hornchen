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

    colors = ["Black", "White",
              "lGray", "Gray", "dGray",
              "Red", "Green", "Blue",
              "Yellow", "Cyan", "Purple2",
              "Magenta", "Pink", "Purple",
              "lBlue", "dBlue", "eBlue",
              "lPink"]
    
    @classmethod
    def with_alpha(self, alpha):
        return _ColorWithAlpha(alpha)

    def by_name(self, name):
        name_lower = name.lower()
        assert name_lower in self.COLORS
        return getattr(self, name_lower)

_DUMMY = Color()

class _ColorWithAlpha:
    def __init__(self, alpha):
        self.alpha = alpha
    
    def __getattr__(self, name):
        return _DUMMY.by_name(name) + (self.alpha, )
        
