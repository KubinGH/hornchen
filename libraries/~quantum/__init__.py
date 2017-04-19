import warnings

sfml_present = pygame_present = False

try:
    import sfml
    from . import pysfml_wrap
except ImportError as e:
    warnings.warn("pySFML was not found")
else:
    sfml_present = True

try:
    import pygame
    from . import pygame_wrap
except ImportError as e:
    print(e)
else:
    pygame_present = True

if sfml_present:
    from .pysfml_wrap import *
elif pygame_present:
    from .pygame_wrap import *
else:
    raise ImportError("Couldn't find any valid game library (pySFML, pygame)")