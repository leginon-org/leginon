from distutils.core import setup, Extension
import glob

setup(
	name='Leginon',
	version='0.9',
	url='http://nramm.scripps.edu/',
	description=
		'Automated data acquisition for transmission electron microscopes',
	packages=['Leginon', 'Leginon.gui', 'Leginon.gui.wx'],
	package_dir={'Leginon': ''},
	data_files=[('config', ['config/default.cfg']),
							('icons', glob.glob('icons/*.png'))],
)

