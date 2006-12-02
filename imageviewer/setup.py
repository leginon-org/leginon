from distutils.core import setup
from distutils.command.install_data import install_data
import glob

class InstallData(install_data):
	def run(self):
		installcommand = self.get_finalized_command('install')
		self.install_dir = installcommand.install_lib
		return install_data.run(self)

setup(
    name='ImageViewer',
    version='0.1',
    description='An image viewer package for wxPython',
    author='Christian Suloway',
    author_email='suloway@caltech.edu',
    maintainer='Christian Suloway',
    maintainer_email='suloway@caltech.edu',
    url='http://www.jensenlab.caltech.edu/',
    packages=['ImageViewer', 'ImageViewer.icons'],
    package_dir={'ImageViewer': ''},
    cmdclass={'install_data': InstallData},
    data_files=[
		('ImageViewer/icons', glob.glob('icons/*.png'))
	]
)
