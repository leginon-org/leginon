from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import sys

if sys.platform == 'win32':
	pl = get_python_lib(True)
	module = Extension(
		'TecnaiCCDWrapper',
		include_dirs=['%s/win32/include' % pl, '%s/win32com/include' % pl],
		library_dirs=['%s/win32/libs' % pl, '%s/win32com/libs' % pl],
		sources=['TecnaiCCDWrapper/TecnaiCCDWrapper.cpp']
	)
	ext_package = 'pyScope'
	ext_modules = [module]
	scripts = ['install-pyscope.py']
else:
	ext_package = None
	ext_modules = None
	scripts = []

setup(
	name='pyScope',
	version='1.0.3',
	description='Interface to Electron Microscopes and CCD Cameras',
	packages=['pyScope'],
	package_dir={'pyScope': ''},
	ext_package=ext_package,
	ext_modules=ext_modules,
	scripts=scripts,
)

