# For more info on expanding this script, see:
#     http://docs.python.org/distutils/setupscript.html

import os
import glob
import distutils.core

#--install-scripts=/usr/local/bin

version = None
verfile = 'appionlib/version.txt'
if os.path.isfile(verfile):
	f = open(verfile, "r")
	line = f.readline()
	f.close()
	version = line.strip()

distutils.core.setup(
	name='Appion',
	version=version,
	author_email='appion@scripps.edu',
	packages=['appionlib', 'appionlib.apSpider', 'appionlib.apTilt', 'appionlib.apImage'],
	package_data={'appionlib': ['data/*.*', 'version.txt']},
	scripts=glob.glob('bin/*.py'),
)

