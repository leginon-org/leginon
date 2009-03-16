from distutils.core import setup

setup(
	name='comarray',
	version='1.0.0',
	description='get numpy array from COM object',
	packages=['comarray'],
	package_dir={'comarray': 'py'},
	package_data={'comarray': ['NumpySafeArray.pyd']}
)

