from distutils.core import setup, Extension
from numarray.numarrayext import NumarrayExtension

module = NumarrayExtension('mser',sources=['mserpy.c','mser.c','ellipsefit.c','lautil.c','util.c','csift.c','mutil.c','image.c','match.c','unionfind.c','mserutil.c'])

setup(
	name='mser',
	version='0.1a',
	description='wrapper around craigmser',
	ext_modules=[module]
)

