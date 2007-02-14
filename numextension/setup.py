from distutils.core import setup, Extension
from numarray.numarrayext import NumarrayExtension

module = NumarrayExtension('numextension', sources = ['numextension.c', 'canny_edge.c'])

setup(
	name='NumExtension',
	version='1.0.3',
	description='Extensions to numpy',
	url='http://nramm.scripps.edu/',
	ext_modules=[module]
)

