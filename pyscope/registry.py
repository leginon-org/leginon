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

temorder = []
tems = {}
ccdcameraorder = []
ccdcameras = {}

def register(module):
	classes = inspect.getmembers(module, predicate=inspect.isclass)
	for classname, c in classes:
		if issubclass(c, tem.TEM):
			temorder.append((c.name, c))
			tems[c.name] = c
		if issubclass(c, ccdcamera.CCDCamera):
			ccdcameraorder.append((c.name, c))
			ccdcameras[c.name] = c

def getClass(name):
	if name in tems:
		return tems[name]
	elif name in ccdcameras:
		return ccdcameras[name]
	else:
		return None

def getClasses():
	return temorder + ccdcameraorder

import tecnai
register(tecnai)

try:
	import CM
	register(CM)
except:
	pass

try:
	import gatan
	register(gatan)
except:
	pass

try:
	import tietz
	register(tietz)
except:
	pass

try:
	import tia
	register(tia)
except:
	pass

import simtem
register(simtem)

import simccdcamera
register(simccdcamera)

#import filmscanner
#register(filmscanner)
