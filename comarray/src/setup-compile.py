from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import sys

pl = get_python_lib(True)

numpysafearray = Extension(
	'NumpySafeArray',
	include_dirs=['%s/win32/include' % pl, '%s/win32com/include' % pl, '%s/numpy/core/include' % pl],
	library_dirs=['%s/win32/libs' % pl, '%s/win32com/libs' % pl],
	sources=['NumpySafeArray.cpp']
)
ext_modules = [numpysafearray]
ext_package = 'NumpySafeArray'

setup(
	name='NumpySafeArray',
	version='1.0.0',
	description='get numpy array from COM object',
	packages=['NumpySafeArray'],
	package_dir={'NumpySafeArray': ''},
	ext_package=ext_package,
	ext_modules=ext_modules,
)

