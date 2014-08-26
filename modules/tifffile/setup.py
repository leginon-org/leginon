#!/usr/bin/env python

# Usage: ``python setup.py build_ext --inplace``
from distutils.core import setup, Extension
import numpy
setup(name='_tifffile',
        ext_modules=[Extension('_tifffile', ['tifffile.c'],
                               include_dirs=[numpy.get_include()])],
        version='2013.11.05',
        description='Python C extension module for decoding PackBits and LZW encoded TIFF data',
)
