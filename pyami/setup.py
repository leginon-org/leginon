from distutils.core import setup

setup(
	name='pyami',
	version='0.1',
	description='Core Python tools for AMI Group',
	packages=['pyami', 'pyami.fft', 'pyami.fft.fftw3'],
	package_dir={'pyami': ''},
	scripts=['mrc2any', 'any2mrc', 'timedproc.py', 'fft/fftwsetup.py'],
)
