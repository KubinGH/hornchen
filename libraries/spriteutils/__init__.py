import warnings

assert __name__ != "__main__", "This script will not work correctly if run directly"

use_cython = use_pyximport = use_python = False

def error_msg(error):
    return "{}: {}".format(type(error).__name__, str(error))

try:
    # Try importing compiled Cython (.pyd file)
    from . import cyspriteutils
except Exception as e:
    warnings.warn("Couldn't find a compiled Cython spriteutils version")    
    try:
        # Try compiling Cython source (.pyx) on runtime to
        # pyxbuild subdirectory (of this script directory)
        import pyximport, os
        script_dir = os.path.dirname(os.path.realpath(__file__))
        build_dir = os.path.join(script_dir, "pyxbuild")
        pyximport.install(language_level=3, build_dir=build_dir)
        from . import cyspriteutils
    except Exception as e:
        warnings.warn("Couldn't compile a Cython spriteutils on run-time")
    else:
        use_pyximport = True
else:
    use_cython = True

try:
    # Try importing the Python version (may cause errors later)
    from . import pyspriteutils
except Exception as e:
    warnings.warn("Couldn't import a Python spriteutils")
else:
    use_python = True

if use_python:
    from .pyspriteutils import *
if use_cython or use_pyximport:
    # Override some of the Python implementation with Cython
    from .cyspriteutils import *
    cydir = dir(cyspriteutils)
    for obj in dir(pyspriteutils):
        if not obj.startswith("_") and obj not in cydir:
            msg = "Object {} not found in Cython version, falling back to Python implementation".format(obj)
            warnings.warn(msg)
            
if not any((use_cython, use_pyximport, use_python)):
    raise ImportError("Couldn't find any valid spriteutils")
