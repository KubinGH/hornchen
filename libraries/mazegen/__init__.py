import warnings

assert __name__ != "__main__", "This script will not work correctly if run directly"

use_cython = use_pyximport = use_python = False

def error_msg(error):
    return "{}: {}".format(type(error).__name__, str(error))

try:
    # Try importing compiled Cython (.pyd file)
    from . import cymaze
except Exception as e:
    warnings.warn("Couldn't find a compiled Cython maze generator version")
    try:
        # Try compiling Cython source (.pyx) on runtime to
        # pyxbuild subdirectory (of this script directory)
        import pyximport, os
        script_dir = os.path.dirname(os.path.realpath(__file__))
        build_dir = os.path.join(script_dir, "pyxbuild")
        pyximport.install(language_level=3, build_dir=build_dir)
        from . import cymaze
    except Exception as e:
        warnings.warn("Couldn't compile a Cython maze generator on run-time")
        try:
            # Try importing the Python version (may cause errors later)
            from . import pymaze
            use_python = True
        except Exception as e:
            warnings.warn("Couldn't import a Python maze generator")
    else:
        use_pyximport = True
else:
    use_cython = True

if use_cython or use_pyximport:
    from .cymaze import *
elif use_python:
    from .pymaze import *

if not any((use_cython, use_pyximport, use_python)):
    raise ImportError("Couldn't find any valid maze generator")
