# For more info on expanding this script, see:
#     http://docs.python.org/distutils/setupscript.html

import sys
import os
import glob
import distutils.core

#--install-scripts=/usr/local/bin/appion

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

# This version information is used to populate a table in the 
# ap databases that stores the revision of the software being used
# for processing. The revision number is available from the svn files
# co-located with the code if the file was retrieved with svn. If this
# is an actual installation that does not have svn files available b/c
# it was installed from a tar file, the version.txt file needs to 
# be located in the appionlib directory and needs to have the svn
# revison number updated by hand prior to release. Ideally this process 
# should be automated in the future. 
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

# script files to be installed in bin dir
binfiles=glob.glob('bin/*.*')

# determine if script destination has been properly specified
arg_cmd = None
arg_install_scripts = False
arg_install_dir = False
arg_help = False
for arg in sys.argv:
	if arg == 'install':
		arg_cmd = 'install'
	if arg == 'install_scripts':
		arg_cmd = 'install_scripts'
	if 'install-scripts' in arg:
		arg_install_scripts = True
	if 'install-dir' in arg:
		arg_install_dir = True
	if 'help' in arg:
		arg_help = True
warn_user = ''
if not arg_help:
	if arg_cmd == 'install' and not arg_install_scripts:
		warn_user = '--install-scripts'
	if arg_cmd == 'install_scripts' and not arg_install_dir:
		warn_user = '--install_dir'
if warn_user:
	message = '''   *** WARNING ***
  You have not specified the option:  %s=<scriptpath>
  You are about to install %d scripts into the default script directory.
  The default could be /usr/bin, /usr/local/bin, or some other location
  you do not wish to clutter up with these scripts.

  Are you sure you want to continue? (y/n): ''' % (warn_user, len(binfiles))
	answer = raw_input(message)
	if answer != 'y':
		print 'Installation aborted.'
		sys.exit()

distutils.core.setup(
	name='Appion',
	version=version,
	author_email='appion@scripps.edu',
	packages=['appionlib', 'appionlib.apSpider', 'appionlib.apTilt', 'appionlib.apImage', 'appionlib.apImagic', 'appionlib.apCtf'],
	package_data={'appionlib': ['data/*.*', 'version.txt']},
	scripts=binfiles,
)

