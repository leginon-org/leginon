from distutils.core import setup

setup(
	name='slack',
	version='0.1',
	description='slack client hook',
	packages=['slack'],
	package_dir={'slack': ''},
	scripts = ['slack_test.py',],
)
