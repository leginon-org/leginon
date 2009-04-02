from distutils.core import setup
from distutils.command.install_data import install_data
import sys

class InstallData(install_data):
	def run(self):
		installcommand = self.get_finalized_command('install')
		self.install_dir = installcommand.install_lib
		return install_data.run(self)

if sys.platform == 'win32':
	scripts = ['install-pyscope.py']
else:
	scripts = []

setup(
	name='pyScope',
	version='1.0.8',
	description='Interface to Electron Microscopes and CCD Cameras',
	cmdclass={'install_data':InstallData},
	packages=['pyScope'],
	package_dir={'pyScope': ''},
	scripts=scripts,
	data_files=[
		('pyScope', ['instruments.cfg']),
	]
)

