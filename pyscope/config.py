#!/usr/bin/env python

import sys
import ConfigParser
import imp
import os
import tem
import ccdcamera

configparser = ConfigParser.SafeConfigParser()

# use the path of this module
modpath = os.path.dirname(__file__)

# read instruments.cfg
filename = os.path.join(modpath, 'instruments.cfg')
if not os.path.exists(filename):
	print 'please configure %s' % (filename,)
	sys.exit()
try:
	configparser.read([filename])
except:
	print 'error reading %s' % (filename,)
	sys.exit()

# parse
names = configparser.sections()
temclasses = []
cameraclasses = []
for name in names:
	cls_str = configparser.get(name, 'class')
	modname,clsname = cls_str.split('.')
	fullmodname = 'pyscope.' + modname
	args = imp.find_module(modname, [modpath])
	try:
		mod = imp.load_module(fullmodname, *args)
	finally:
		if args[0] is not None:
			args[0].close()
	cls = getattr(mod, clsname)
	if issubclass(cls, tem.TEM):
		temclasses.append(cls)
	if issubclass(cls, ccdcamera.CCDCamera):
		cameraclasses.append(cls)

print temclasses
print cameraclasses
