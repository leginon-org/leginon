import glob
import os
from distutils.command.install_data import install_data
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
import version

class InstallData(install_data):
	def run(self):
		installcommand = self.get_finalized_command('install')
		self.install_dir = installcommand.install_lib
		return install_data.run(self)

setup(
	name='Leginon',
	version=version.getVersion(),
	url='http://nramm.scripps.edu/',
	description=
		'Automated data acquisition for transmission electron microscopes',
	cmdclass={'install_data': InstallData},
	packages=['Leginon', 'Leginon.gui', 'Leginon.gui.wx', 'Leginon.icons'],
	package_dir={'Leginon': ''},
	data_files=[
		('Leginon/config', ['config/default.cfg']),
		('Leginon/icons', glob.glob('icons/*.png')),
		('Leginon/icons/processing', glob.glob('icons/processing/*.png')),
	],
	scripts=['install-leginon.py', 'start-leginon.py'],
)

