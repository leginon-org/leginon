## Sorry for the following mess, but I insist on being able to use
## numextension immediately after a build, without an install.

import imp
import sys
import os.path

packagename = 'numextension'
modulename = '_numextension'
fullname = '.'.join([packagename, modulename])
packagemod = sys.modules[packagename]
packagepath = __path__[0]
_numextension = None

try:
	## If package was actually installed, this will work...
	import _numextension
	from _numextension import *

except ImportError:
	# Maybe it was built, but not installed, then we look in build directory
	build_dir = os.path.join(packagepath, 'build')
	if os.path.exists(build_dir):
		args = None
		for dirpath, dirnames, filenames in os.walk(build_dir):
			try:
				args = imp.find_module(modulename, [dirpath])
				break
			except:
				pass
		if args:
			_numextension = imp.load_module(fullname, *args)
			from _numextension import *

if _numextension is None:
	raise ImportError('Numextension package cannot be used until you build it.  Go into numextension and run "python setup.py build" (or install, if you wish).')

# clean up temp attrs
for attr in ('packagename', 'modulename', 'fullname', 'imp', 'sys', '_numextension', 'args', 'os', 'dirpath', 'dirnames', 'filenames', 'build_dir', 'packagepath'):
	if attr in packagemod.__dict__:
		del packagemod.__dict__[attr]
del packagemod
del attr
