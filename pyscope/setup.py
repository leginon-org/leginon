from distutils.core import setup
import sys

if sys.platform == 'win32':
	scripts = ['install-pyscope.py']
else:
	scripts = []

setup(
	name='pyScope',
	version='1.0.8',
	description='Interface to Electron Microscopes and CCD Cameras',
	packages=['pyScope'],
	package_dir={'pyScope': ''},
	scripts=scripts,
	data_files=[
		('pyScope', ['instruments.cfg']),
	]
)

