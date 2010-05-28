from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import sys

pl = get_python_lib(True)

numpysafearray = Extension(
	'comarray._numpysafearray',
	include_dirs=['%s/win32/include' % pl, '%s/win32com/include' % pl, '%s/numpy/core/include' % pl],
	library_dirs=['%s/win32/libs' % pl, '%s/win32com/libs' % pl],
	sources=['numpysafearray.cpp']
)
ext_modules = [numpysafearray]

setup(
	name='comarray',
	version='2.0.0',
	description='get numpy array from COM object',
	packages=['comarray'],
	package_dir={'comarray': ''},
	ext_modules=ext_modules,
)

