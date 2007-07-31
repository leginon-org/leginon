from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import sys

if sys.platform == 'win32':
	pl = get_python_lib(True)

	#numarraysafearray = Extension(
	#	'NumarraySafeArray',
	#	include_dirs=['%s/win32/include' % pl, '%s/win32com/include' % pl],
	#	library_dirs=['%s/win32/libs' % pl, '%s/win32com/libs' % pl],
	#	sources=['NumSafeArray/NumarraySafeArray.cpp']
	#)
	#ext_modules = [numarraysafearray]
	ext_package = 'pyScope'
	scripts = ['install-pyscope.py']
else:
	ext_package = None
	ext_modules = None
	scripts = []

setup(
	name='pyScope',
	version='1.0.7',
	description='Interface to Electron Microscopes and CCD Cameras',
	packages=['pyScope'],
	package_dir={'pyScope': ''},
	ext_package=ext_package,
	ext_modules=ext_modules,
	scripts=scripts,
)

