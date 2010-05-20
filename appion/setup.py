# For more info on expanding this script, see:
#     http://docs.python.org/distutils/setupscript.html

import os
import glob
import distutils.core

#--install-scripts=/usr/local/bin

def getSubversionRevision():
	if not os.path.isfile(".svn/entries"):
		return None
	### use fourth line from entries file
	f = open(".svn/entries", "r")
	for i in range(4):
		line = f.readline()
	revision = "r"+line.strip()
	f.close()
	return revision

def getVersion():
	prettyversion = None
	verfile = 'appionlib/version.txt'
	if os.path.isfile(verfile):
		f = open(verfile, "r")
		line = f.readline()
		f.close()
		prettyversion = line.strip()
	revision = getSubversionRevision()
	if prettyversion is not None and revision is not None:
		version = "%s-%s"%(prettyversion, revision)
	elif revision is not None:
		version = revision
		### write revision to file
		f = open(verfile, "w")
		f.write("%s\n"%(revision))
		f.close()
	elif prettyversion is not None:
		version = prettyversion
	else:
		raise VersionError, "cound not find appion version number"
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

