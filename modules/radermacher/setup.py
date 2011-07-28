#!/usr/bin/python

from distutils.core import setup
from numpy.distutils.extension import Extension
import numpy

numpyinc = numpy.get_include()

module = Extension(
	'radermacher', 
	sources = ['main.c', 'tiltang.c', 'willsq.c', 'transform.c', 'radon.c',], 
	include_dirs=[numpyinc,],
	extra_compile_args=['-fopenmp',],
	extra_link_args=['-lgomp',],
)

setup(
	name='Radermacher',
	version='1.1',
	description='Radermacher functions for use in Appion',
	author='Neil R. Voss',
	author_email='vossman77@yahoo.com',
	url='http://ami.scripps.edu/redmine/projects/appion/wiki/Compile_Radermacher',
	license="Apache v2.0",
	ext_modules=[module]
)

