from distutils.core import setup
import glob

setup(
    name='Image Viewer',
    version='0.1',
    description='An image viewer package for wxPython',
    author='Christian Suloway',
    author_email='suloway@caltech.edu',
    maintainer='Christian Suloway',
    maintainer_email='suloway@caltech.edu',
    url='http://www.jensenlab.caltech.edu/',
    packages=['ImageViewer', 'ImageViewer.icons'],
    package_dir={'ImageViewer': ''},

	data_files=[
		('ImageViewer/icons', glob.glob('icons/*.png'))
	]
)
