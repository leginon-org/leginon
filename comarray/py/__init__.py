import sys

# use precompiled NumpySafeArray dll only if python 2.5
v = sys.version_info
if v[:2] == (2,5):
	from NumpySafeArray import *
else:
	from NumpySafeArraySlow import *
