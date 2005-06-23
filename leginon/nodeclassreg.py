#
# COPYRIGHT:
#		The Leginon software is Copyright 2003
#		The Scripps Research Institute, La Jolla, CA
#		For terms of the license agreement
#		see  http://ami.scripps.edu/software/leginon-license
#
### this module is used as a container for all node classes
import node
import imp
import sys
import os
import os.path
import ConfigParser

reg_dict = {}
reg_list = []
sortclasses = {}

class NodeRegistryError(Exception):
	pass

class NotFoundError(NodeRegistryError):
	pass

class InvalidNodeError(NodeRegistryError):
	pass

def registerNodeClass(modulename, classname, sortclass=None, package=None):
	# ...
	if package is None:
		path = None
	else:
		try:
			file, path, desc = imp.find_module(package)
		except ImportError, detail:
			raise NotFoundError('package \'%s\' not found' % package)
		try:
			path = imp.load_module(package, file, path, desc).__path__
		except Exception, detail:
			raise
	### find the module
	try:
		modinfo = imp.find_module(modulename, path)
	except ImportError, detail:
		raise NotFoundError('module \'%s\' not found' % modulename)

	### import the module
	try:
		if package is None:
			mod = imp.load_module(modulename, *modinfo)
		else:
			mod = imp.load_module(package + '.' + modulename, *modinfo)
	except Exception, detail:
		raise

	### get the class from the module
	try:
		nodeclass = getattr(mod, classname)
	except AttributeError, detail:
		message = 'class %s not found in module \'%s\'' % (classname, modulename)
		raise NotFoundError(message)

	### make sure class is Node
	if not issubclass(nodeclass, node.Node):
		raise InvalidNodeError('%s is not subclass of node.Node' % nodeclass)

	### everything worked, record this in the registry
	reg_dict[classname] = {'module': mod}
	reg_list.append(classname)
	if sortclass not in sortclasses:
		sortclasses[sortclass] = []
	sortclasses[sortclass].append(classname)

def getNodeClass(classname):
	if classname not in reg_dict:
		raise NotFoundError('\'%s\' not in registry' % classname)
	mod = reg_dict[classname]['module']
	#reload(mod)
	return getattr(mod, classname)

def getNodeClassNames():
	return reg_list

def getSortClass(clsname):
	for key, value in sortclasses.items():
		if clsname in value:
			return value.index(clsname), key
	return None, None

def registerNodeClasses():
	registrydir = os.path.join(os.path.dirname(__file__), 'noderegistry')
	configfiles = []
	for filename in os.listdir(registrydir):
		root, ext = os.path.splitext(filename)
		if ext == '.ncr':
			if root == 'default':
				configfiles.insert(0, os.path.join(registrydir, filename))
			else:
				configfiles.append(os.path.join(registrydir, filename))
	configparser = ConfigParser.SafeConfigParser()
	configparser.read(configfiles)
	for classname in configparser.sections():
		try:
			modulename = configparser.get(classname, 'module')
		except ConfigParser.NoOptionError:
			continue
		try:
			sortclass = configparser.get(classname, 'type')
		except ConfigParser.NoOptionError:
			sortclass = None
		try:
			package = configparser.get(classname, 'package')
		except ConfigParser.NoOptionError:
			package = None
		registerNodeClass(modulename, classname, sortclass, package)

registerNodeClasses()

'''
### register Node classes in the order you want them listed publicly
registerNodeClass('EM', 'EM', 'Utility')
registerNodeClass('corrector', 'Corrector', 'Utility')
registerNodeClass('presets', 'PresetsManager', 'Utility')
registerNodeClass('driftmanager', 'DriftManager', 'Utility')
registerNodeClass('navigator', 'Navigator', 'Utility')
registerNodeClass('manualacquisition', 'ManualAcquisition', 'Utility')
registerNodeClass('robotatlastargetfinder', 'RobotAtlasTargetFinder', 'Utility')
registerNodeClass('intensitymonitor', 'IntensityMonitor', 'Utility')

registerNodeClass('pixelsizecalibrator', 'PixelSizeCalibrator', 'Calibrations')
registerNodeClass('dosecalibrator', 'DoseCalibrator', 'Calibrations')
registerNodeClass('matrixcalibrator', 'MatrixCalibrator', 'Calibrations')
registerNodeClass('beamtiltcalibrator', 'BeamTiltCalibrator', 'Calibrations')
registerNodeClass('gonmodeler', 'GonModeler', 'Calibrations')

registerNodeClass('robot', 'Robot', 'Pipeline')
registerNodeClass('atlastargetmaker', 'AtlasTargetMaker', 'Pipeline')
registerNodeClass('targetmaker', 'MosaicTargetMaker', 'Pipeline')
registerNodeClass('acquisition', 'Acquisition', 'Pipeline')
registerNodeClass('targetfinder', 'MosaicClickTargetFinder', 'Pipeline')
registerNodeClass('focuser', 'Focuser', 'Pipeline')
registerNodeClass('targetfinder', 'ClickTargetFinder', 'Pipeline')
registerNodeClass('holefinder', 'HoleFinder', 'Pipeline')
registerNodeClass('rasterfinder', 'RasterFinder', 'Pipeline')
registerNodeClass('matlabtargetfinder', 'MatlabTargetFinder', 'Pipeline')
registerNodeClass('fftmaker', 'FFTMaker', 'Pipeline')

# need new interface
#registerNodeClass('emailnotification', 'Email')
#registerNodeClass('squarefinder', 'SquareFinder', 'Pipeline')
#registerNodeClass('squarefinder2', 'SquareFinder2', 'Pipeline')

# not fully implemented
#registerNodeClass('intensitycalibrator', 'IntensityCalibrator', 'Calibrations')
#registerNodeClass('webcam', 'Webcam', 'Utility')
'''

