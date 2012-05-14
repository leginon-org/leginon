#!/usr/bin/env python

import sys
import ConfigParser
import imp
import os
import inspect
import pyscope
import pyscope.tem
import pyscope.ccdcamera

configured = None
temclasses = None
cameraclasses = None

def parse():
	global configured, temclasses, cameraclasses

	configparser = ConfigParser.SafeConfigParser()

	# use the path of this module
	modpath = pyscope.__path__

	# read instruments.cfg
	filename = os.path.join(modpath[0], 'instruments.cfg')
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
	configured = {}
	mods = {}

	for name in names:
		configured[name] = {}
		cls_str = configparser.get(name, 'class')
		modname,clsname = cls_str.split('.')
		if modname not in mods:
			fullmodname = 'pyscope.' + modname
			args = imp.find_module(modname, modpath)
			try:
				mod = imp.load_module(fullmodname, *args)
			finally:
				if args[0] is not None:
					args[0].close()
			mods[modname] = mod
		mod = mods[modname]
		cls = getattr(mod, clsname)
		if issubclass(cls, pyscope.tem.TEM):
			try:
				cs_str = configparser.get(name, 'cs')
				cs_value = float(cs_str)
			except:
				cs_value = None
			configured[name]['cs'] = cs_value
			temclasses.append(cls)
		if issubclass(cls, pyscope.ccdcamera.CCDCamera):
			try:
				z_str = configparser.get(name, 'zplane')
				z_value = int(z_str)
			except:
				z_value = 0
			configured[name]['zplane'] = z_value
			cameraclasses.append(cls)
		configured[name]['class'] = cls

	return configured, temclasses, cameraclasses

def getConfigured():
	global configured
	if configured is None:
		parse()
	return configured

def getTEMClasses():
	global temclasses
	if temclasses is None:
		parse()
	return temclasses

def getCameraClasses():
	global cameraclasses
	if cameraclasses is None:
		parse()
	return cameraclasses
	
def getNameByClass(cls):
	conf = getConfigured()
	for bcls in inspect.getmro(cls):
		for name,value in conf.items():
			if bcls is value['class']:
				return name
