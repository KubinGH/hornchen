from distutils.core import setup
from Cython.Build import cythonize
setup(ext_modules=cythonize(r'C:\Users\Admin\Desktop\Hornchen\libraries\spriteutils\cyspriteutils.pyx', language_level=3))