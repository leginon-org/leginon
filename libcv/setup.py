#!/usr/bin/python

from distutils.core import setup
from distutils.util import get_platform
from numpy.distutils.extension import Extension
import numpy

if get_platform() == 'win32':
	define_macros=[]
else:
	define_macros=[('HAS_RUSAGE', None)]

numpyinc = numpy.get_include()

module = Extension('libCV',sources=['mserpy.c','mser.c','geometry.c','lautil.c','util.c','csift.c','mutil.c','image.c','match.c','unionfind.c'],define_macros=define_macros,include_dirs=[numpyinc,])

setup(
	name='libCV',
	version='0.2',
	description='wrapper around libCV',
	ext_modules=[module]
)

