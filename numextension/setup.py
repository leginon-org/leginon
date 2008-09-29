from distutils.core import setup
from numpy.distutils.extension import Extension
import numpy

numpyinc = numpy.get_include()

module = Extension('numextension', sources = ['numextension.c', 'canny_edge.c'], libraries=['fftw','m'], include_dirs=[numpyinc,])

setup(
	name='NumExtension',
	version='1.1.0',
	description='Extensions to numpy',
	url='http://nramm.scripps.edu/',
	ext_modules=[module]
)

