from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("determine_trade_type.pyx", compiler_directives={"language_level": "3"})
)
