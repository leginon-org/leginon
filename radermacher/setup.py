from distutils.core import setup
from numpy.distutils.extension import Extension
import numpy

numpyinc = numpy.get_include()

module = Extension('radermacher', sources = ['radermacher.c'], include_dirs=[numpyinc,])

setup(
	name='Radermacher',
	version='0.9',
	description='Radermacher functions',
	url='http://nramm.scripps.edu/',
	ext_modules=[module]
)

