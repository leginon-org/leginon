from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import sys

if sys.platform == 'win32':
	pl = get_python_lib(True)
	ext_package = 'pyscope'
	scripts = ['install-pyscope.py']
else:
	ext_package = None
	scripts = []

setup(
	name='pyscope',
	version='1.0.8',
	description='Interface to Electron Microscopes and CCD Cameras',
	packages=['pyscope'],
	package_dir={'pyscope': ''},
	ext_package=ext_package,
	scripts=scripts,
)

