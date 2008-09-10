from distutils.core import setup

setup(
	name='pyami',
	version='0.1',
	description='Core Python tools for AMI Group',
	packages=['pyami'],
	package_dir={'pyami': ''},
	scripts=['mrc2any', 'any2mrc'],
)
