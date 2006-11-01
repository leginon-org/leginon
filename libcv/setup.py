from distutils.core import setup, Extension
from numarray.numarrayext import NumarrayExtension
from distutils.util import get_platform

if get_platform() == 'win32':
	define_macros=[]
else:
	define_macros=[('HAS_RUSAGE', None)]

module = NumarrayExtension('libCV',sources=['mserpy.c','mser.c','geometry.c','lautil.c','util.c','csift.c','mutil.c','image.c','match.c','unionfind.c'], define_macros=define_macros)

setup(
	name='libCV',
	version='0.1a',
	description='wrapper around libCV',
	ext_modules=[module]
)

