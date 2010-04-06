# For more info on expanding this script, see:
#     http://docs.python.org/distutils/setupscript.html

import distutils.core
import glob

distutils.core.setup(
	name='Appion',
	packages=['appionlib'],
	scripts=glob.glob('bin/*.py'), 
)

