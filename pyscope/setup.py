from distutils.core import setup, Extension
import sys

if sys.platform == 'win32':
	module = Extension(
		'TecnaiCCDWrapper',
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
	version='1.0.1',
	description='Interface to Electron Microscopes and CCD Cameras',
	packages=['pyScope'],
	package_dir={'pyScope': ''},
	ext_package=ext_package,
	ext_modules=ext_modules,
	scripts=scripts,
)

