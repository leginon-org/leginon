#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import inspect
import tem
import ccdcamera

tems = {}
ccdcameras = {}

def register(module):
	classes = inspect.getmembers(module, predicate=inspect.isclass)
	for classname, c in classes:
		if issubclass(c, tem.TEM):
			tems[c.name] = c
		if issubclass(c, ccdcamera.CCDCamera):
			ccdcameras[c.name] = c

def getClass(name):
	if name in tems:
		return tems[name]
	elif name in ccdcameras:
		return ccdcameras[name]
	else:
		return None

def getClasses():
	return tems.items() + ccdcameras.items()

import tecnai
register(tecnai)

import gatan
register(gatan)

import tietz
register(tietz)

