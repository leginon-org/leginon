#!/usr/bin/python

from distutils.core import setup
from numpy.distutils.extension import Extension
import numpy

numpyinc = numpy.get_include()

module = Extension(
	 'radermacher', 
	 sources = ['main.c', 'tiltang.c', 'willsq.c', 'transform.c'], 
	 include_dirs=[numpyinc,]
	)

setup(
	name='Radermacher',
	version='0.1',
	description='Radermacher functions',
	url='http://nramm.scripps.edu/',
	ext_modules=[module]
)

