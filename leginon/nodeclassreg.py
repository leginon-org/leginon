### this module is used as a container for all node classes

import node
import imp

reg_dict = {}
reg_list = []

def registerNodeClass(modulename, classname):
	### find the module
	try:
		modinfo = imp.find_module(modulename)
	except ImportError, detail:
		print '### Module not found: %s' % modulename
		print '    %s' % detail
		return

	### import the module
	try:
		mod = imp.load_module(modulename, *modinfo)
	except Exception, detail:
		print '### Exception while importing %s' % modulename
		print '    %s' % detail
		return

	### get the class from the module
	try:
		nodeclass = getattr(mod, classname)
	except AttributeError, detail:
		print '### Class %s not in module %s' % (classname, modulename)
		print '    %s' % detail
		return

	### make sure class is Node
	if not issubclass(nodeclass, node.Node):
		print '### %s is not subclass of node.Node' % nodeclass
		return

	### everything worked, record this in the registry
	reg_dict[classname] = {'module': mod}
	reg_list.append(classname)

def getNodeClass(classname):
	if classname not in reg_dict:
		print '%s not in registry' % classname
		return None
	mod = reg_dict[classname]['module']
	reload(mod)
	return getattr(mod, classname)

def getNodeClassNames():
	return reg_list


### register Node classes in the order you want them listed publicly
#registerNodeClass('webcam', 'Webcam')
registerNodeClass('EM', 'EM')
registerNodeClass('corrector', 'Corrector')
registerNodeClass('calibration', 'StageShiftCalibration')
registerNodeClass('calibration', 'ImageShiftCalibration')
registerNodeClass('gonmodeler', 'GonModeler')
#registerNodeClass('acquireloop', 'AcquireLoop')
registerNodeClass('navigator', 'SimpleNavigator')
registerNodeClass('imviewer', 'ImViewer')
registerNodeClass('shiftmeter', 'ShiftMeter')
registerNodeClass('gridpreview', 'GridPreview')
#registerNodeClass('watcher', 'TestWatch')
#registerNodeClass('timedloop', 'TestLoop')
#registerNodeClass('getdata', 'GetData')
#registerNodeClass('intgen', 'IntGen')
#registerNodeClass('calibrationtest', 'CalibrationTest')
registerNodeClass('autofocus', 'AutoFocusCalibration')
registerNodeClass('imagemosaic', 'ImageMosaic')
registerNodeClass('imagemosaic', 'StateImageMosaic')
registerNodeClass('testmosaic', 'TestMosaic')
registerNodeClass('mosaicnavigator', 'MosaicNavigator')
registerNodeClass('imagenode', 'ImageNode')


