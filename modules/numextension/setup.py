from distutils.core import setup
from numpy.distutils.extension import Extension
import numpy

numpyinc = numpy.get_include()

numextmod = Extension('numextension._numextension', sources = ['numextension.c', 'canny_edge.c'], include_dirs=[numpyinc])

setup(
	name='numextension',
	description='Extension to numpy',
	ext_modules=[numextmod],
	packages=['numextension'],
	package_dir={'numextension': ''},
	version='svn',
)

