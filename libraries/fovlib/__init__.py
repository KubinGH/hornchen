import warnings

enable_warnings = False

assert __name__ != "__main__", "This script will not work correctly if run directly"

if not enable_warnings:
    warnings.warn = lambda *args, **kwargs: None

use_cython = use_pyximport = use_python = False

def error_msg(error):
    return "{}: {}".format(type(error).__name__, str(error))

try:
    # Try importing compiled Cython (.pyd file)
    from . import cyfovlib
except Exception as e:
    warnings.warn("Couldn't find a compiled Cython fovlib version")    
    try:
        # Try compiling Cython source (.pyx) on runtime to
        # pyxbuild subdirectory (of this script directory)
        import pyximport, os
        script_dir = os.path.dirname(os.path.realpath(__file__))
        build_dir = os.path.join(script_dir, "pyxbuild")
        pyximport.install(language_level=3, build_dir=build_dir)
        from . import cyfovlib
    except Exception as e:
        warnings.warn("Couldn't compile a Cython fovlib on run-time")
    else:
        use_pyximport = True
else:
    use_cython = True

try:
    # Try importing the Python version (may cause errors later)
    from . import pyfovlib
except Exception as e:
    warnings.warn("Couldn't import a Python fovlib")
else:
    use_python = True

if use_python:
    from .pyfovlib import *
if use_cython or use_pyximport:
    # Override some of the Python implementation with Cython
    from .cyfovlib import *
    cydir = dir(cyfovlib)
    for obj in dir(pyfovlib):
        if not obj.startswith("_") and obj not in cydir:
            msg = "Object {} not found in Cython version, falling back to Python implementation".format(obj)
            warnings.warn(msg)

if not any((use_cython, use_pyximport, use_python)):
    raise ImportError("Couldn't find any valid fovlib")
