from distutils.core import setup, Extension

module = Extension('TecnaiCCDWrapper', sources = ['TecnaiCCDWrapper.cpp'])

setup(
	name='TecnaiCCD Wrapper',
	version='1.0',
	description='Wrapper for TecnaiCCD',
	ext_modules=[module]
)

