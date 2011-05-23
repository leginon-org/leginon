#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import config

temorder = []
tems = {}
ccdcameraorder = []
ccdcameras = {}

for c in config.getTEMClasses():
	temorder.append((c.name, c))
	tems[c.name] = c
for c in config.getCameraClasses():
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

