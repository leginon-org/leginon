## Sorry for the following mess, but I insist on being able to use
## libcv immediately after a build, without an install.

import imp
import sys
import os.path

packagename = 'libcv'
modulename = '_libcv'
fullname = '.'.join([packagename, modulename])
packagemod = sys.modules[packagename]
packagepath = __path__[0]
_libcv = None

try:
	## If package was actually installed, this will work...
	import _libcv
	from _libcv import *

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
			_libcv = imp.load_module(fullname, *args)
			from _libcv import *

if _libcv is None:
	raise ImportError('libcv package cannot be used until you build it.  Go into libcv and run "python setup.py build" (or install, if you wish).')

# clean up temp attrs
for attr in ('packagename', 'modulename', 'fullname', 'imp', 'sys', '_libcv', 'args', 'os', 'dirpath', 'dirnames', 'filenames', 'build_dir', 'packagepath'):
	if attr in packagemod.__dict__:
		del packagemod.__dict__[attr]
del packagemod
del attr
