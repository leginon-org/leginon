#!/usr/bin/env python

import sys
import configparser
import imp
import os
import inspect
import pyscope
import pyscope.tem
import pyscope.ccdcamera
import pyami.fileutil

configured = {}
temclasses = None
cameraclasses = None
configfiles = None

def parse():
	global configured, temclasses, cameraclasses, configfiles

	cparser = configparser.ConfigParser()

	# use the path of this module
	modpath = pyscope.__path__

	# read instruments.cfg
	confdirs = pyami.fileutil.get_config_dirs()
	filenames = [os.path.join(confdir, 'instruments.cfg') for confdir in confdirs]
	# take the last existing one only.  This is needed because module name
	# in instruments.cfg is not used.
	filenames = pyami.fileutil.check_exist_one_file(filenames, combine=False)
	try:
		configfiles = cparser.read(filenames)
	except:
		print('error reading %s' % (filenames,))
		sys.exit()

	# parse
	names = cparser.sections()
	temclasses = []
	cameraclasses = []
	mods = {}

	for name in names:
		configured[name] = {}
		cls_str = cparser.get(name, 'class')
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
				cs_str = cparser.get(name, 'cs')
				cs_value = float(cs_str)
			except:
				cs_value = None
			configured[name]['cs'] = cs_value
			temclasses.append(cls)
		if issubclass(cls, pyscope.ccdcamera.CCDCamera):
			cameraclasses.append(cls)
			try:
				z_str = cparser.get(name, 'zplane')
				z_value = int(z_str)
			except:
				z_value = 0
			configured[name]['zplane'] = z_value
			for key in ('height', 'width'):
				try:
					configured[name][key] = int(cparser.get(name, key))
				except:
					pass
		try:
			log = cparser.get(name, 'log')
		except:
			log = None
		configured[name]['log'] = log
		configured[name]['class'] = cls
		# A directory to pass simulated scope parameter to camera
		try:
			simpar_str = cparser.get(name, 'simpar')
			simpar_value = simpar_str
		except:
			simpar_value = None
		configured[name]['simpar'] = simpar_value

	return configured, temclasses, cameraclasses

def getConfigured():
	global configured
	if not configured:
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
		for name,value in list(conf.items()):
			if bcls.__name__ == value['class'].__name__:
				return name
