#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
### this module is used as a container for all node classes
import node
import imp
import sys

reg_dict = {}
reg_list = []
sortclasses = {}

class NodeRegistryError(Exception):
	pass

class NotFoundError(NodeRegistryError):
	pass

class InvalidNodeError(NodeRegistryError):
	pass

def registerNodeClass(modulename, classname, sortclass=None):
	### find the module
	try:
		modinfo = imp.find_module(modulename)
	except ImportError, detail:
		raise NotFoundError('Module \'%s\' not found' % modulename)

	### import the module
	try:
		mod = imp.load_module(modulename, *modinfo)
	except Exception, detail:
		raise

	### get the class from the module
	try:
		nodeclass = getattr(mod, classname)
	except AttributeError, detail:
		message = 'Class %s not found in module \'%s\'' % (classname, modulename)
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

### register Node classes in the order you want them listed publicly
registerNodeClass('EM', 'EM', 'Utility')
registerNodeClass('corrector', 'Corrector', 'Utility')
registerNodeClass('presets', 'PresetsManager', 'Utility')
registerNodeClass('driftmanager', 'DriftManager', 'Utility')
registerNodeClass('navigator', 'Navigator', 'Utility')
registerNodeClass('manualacquisition', 'ManualAcquisition', 'Utility')
registerNodeClass('atlasviewer', 'AtlasViewer', 'Utility')

registerNodeClass('pixelsizecalibrator', 'PixelSizeCalibrator', 'Calibrations')
registerNodeClass('dosecalibrator', 'DoseCalibrator', 'Calibrations')
registerNodeClass('matrixcalibrator', 'MatrixCalibrator', 'Calibrations')
registerNodeClass('beamtiltcalibrator', 'BeamTiltCalibrator', 'Calibrations')
registerNodeClass('gonmodeler', 'GonModeler', 'Calibrations')

registerNodeClass('robot', 'RobotControl', 'Pipeline')
registerNodeClass('robot', 'RobotNotification', 'Pipeline')
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

# depreciated
#registerNodeClass('imviewer', 'ImViewer')
#registerNodeClass('simpleacquisition', 'SimpleAcquisition', 'Pipeline')

