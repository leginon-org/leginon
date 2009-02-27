#!/usr/bin/env python

import sys
import ConfigParser
import imp
import os
import tem
import ccdcamera

configparser = ConfigParser.SafeConfigParser()
modpath = os.path.dirname(__file__)

# look in the same directory as this module
filename = os.path.join(modpath, 'instruments.cfg')
try:
	configparser.read([filename])
except IOError:
	print 'instrument.cfg must be configured for pyScope'
	sys.exit()

names = configparser.sections()
temclasses = []
cameraclasses = []
for name in names:
	cls_str = configparser.get(name, 'class')
	modname,clsname = cls_str.split('.')
	args = imp.find_module(modname, [modpath])
	mod = imp.load_module(modname, *args)
	cls = getattr(mod, clsname)
	if issubclass(cls, tem.TEM):
		temclasses.append(cls)
	if issubclass(cls, ccdcamera.CCDCamera):
		cameraclasses.append(cls)
