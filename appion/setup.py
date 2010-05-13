# For more info on expanding this script, see:
#     http://docs.python.org/distutils/setupscript.html

import os
import glob
import distutils.core

#--install-scripts=/usr/local/bin

def getVersion():
	verfile = 'appionlib/version.txt'
	if not os.path.isfile(verfile):
		if not os.path.isfile(".svn/entries"):
			raise FileError, "Could not find version.txt file"
		### use fourth line from entries file
		f = open(".svn/entries", "r")
		for i in range(4):
			line = f.readline()
		version = "r"+line.strip()
		f.close()
		f = open(verfile, "w")
		f.write("%s\n"%(version))
		f.close()
	f = open(verfile, "r")
	line = f.readline()
	f.close()
	version = line.strip()
	return version

version=getVersion()

distutils.core.setup(
	name='Appion',
	version=version,
	author_email='appion@scripps.edu',
	packages=['appionlib', 'appionlib.apSpider', 'appionlib.apTilt', 'appionlib.apImage'],
	package_data={'appionlib': ['data/*.*', 'version.txt']},
	scripts=glob.glob('bin/*.*'),
)

