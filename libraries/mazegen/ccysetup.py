from distutils.core import setup
from Cython.Build import cythonize
setup(ext_modules=cythonize(r'C:\Users\Admin\Desktop\Rogue\libraries\mazegen\cymaze.pyx', language_level=3))