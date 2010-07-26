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
	packages=['leginon', 'leginon.gui', 'leginon.gui.wx', 'leginon.icons', 'leginon.tomography', 'leginon.gui.wx.tomography', 'leginon.applications'],
	package_dir={'leginon': ''},
	data_files=[
		('leginon', ['holetemplate.mrc']),
		('leginon', ['sq_example.jpg']),
		('leginon', ['hl_example.jpg']),
		('leginon/config', ['config/default.cfg']),
		('leginon/icons', glob.glob('icons/*.png')),
		('leginon/icons/processing', glob.glob('icons/processing/*.png')),
		('leginon/applications', glob.glob('applications/*.xml')),
	],
	scripts=['install-leginon.py', 'start-leginon.py'],
)

