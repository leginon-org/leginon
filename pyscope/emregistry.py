#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import imp

registry = {}
registry['scope'] = {}
registry['camera'] = {}

def findClass(modulename, classname):
	try:
		fp, pathname, description = imp.find_module(modulename)
	except ImportError:
		return None
	module = imp.load_module(modulename, fp, pathname, description)
	try:
		return module.__dict__[classname]
	except KeyError:
		return None

def register(type, name, modulename, classname, description=''):
	registry[type][name] = (modulename, classname, description)

def registerScope(name, modulename, classname, description=''):
	register('scope', name, modulename, classname, description)

def registerCamera(name, modulename, classname, description=''):
	register('camera', name, modulename, classname, description)

def getInfo(type, name):
	try:
		return registry[type][name]
	except KeyError:
		return None

def getScopeInfo(name):
	return getInfo('scope', name)

def getCameraInfo(name):
	return getInfo('camera', name)

def getClass(type, name):
	info = getInfo(type, name)
	if info is None:
		return None
	modulename, classname, description = info
	return findClass(modulename, classname)

def getScopeClass(name):
	return getClass('scope', name)

def getCameraClass(name):
	return getClass('camera', name)

def getNames(type):
	names = registry[type].keys()
	names.sort()
	return names

def getScopeNames():
	return getNames('scope')

def getCameraNames():
	return getNames('camera')

registerScope('Tecnai', 'tecnai', 'Tecnai', 'Tecnai TEM')

registerCamera('Tietz PXL', 'tietz', 'TietzPXL', 'Tietz PXL CCD Camera')
registerCamera('Tietz Simulation', 'tietz', 'TietzSimulation',
								'Tietz Simulation CCD Camera')
registerCamera('Tietz PVCam', 'tietz', 'TietzPVCam', 'Tietz PVCam CCD Camera')
registerCamera('Tietz FastScan', 'tietz', 'TietzFastScan',
								'Tietz FastScan CCD Camera')
registerCamera('Tietz FastScan Firewire', 'tietz', 'TietzFastScanFW',
								'Tietz FastScan Firewire CCD Camera')
registerCamera('Tietz SCX', 'tietz', 'TietzSCX', 'Tietz SCX CCD Camera')
registerCamera('Gatan', 'gatan', 'Gatan', 'Gatan CCD Camera')

