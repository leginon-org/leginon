from distutils.core import setup

setup(
	name='redux',
	packages=['redux', 'redux.pipes', 'redux.pipelines'],
	package_dir={'redux': ''},
	scripts=['bin/reduxd', 'bin/redux'],
)

