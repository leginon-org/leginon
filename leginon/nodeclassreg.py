### this module is used as a container for all node classes

import node
import imp

reg_dict = {}
reg_list = []

def registerNodeClass(modulename, classname):
	try:
		modinfo = imp.find_module(modulename)
	except ImportError:
		print 'Module not found: %s' % modulename
		return

	mod = imp.load_module(modulename, *modinfo)

	try:
		nodeclass = getattr(mod, classname)
	except AttributeError:
		print 'Class %s not in module %s' % (classname, modulename)
		return

	if not issubclass(nodeclass, node.Node):
		raise RuntimeError('not subclass of node: %s' % module_class)

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

registerNodeClass('EM', 'EM')
registerNodeClass('emtest', 'EMTest')
registerNodeClass('calibration', 'Calibration')
registerNodeClass('calibration', 'StageCalibration')
registerNodeClass('calibration', 'ImageShiftCalibration')
registerNodeClass('acquireloop', 'AcquireLoop')
registerNodeClass('navigator', 'Navigator')
registerNodeClass('imviewer', 'ImViewer')
registerNodeClass('shiftmeter', 'ShiftMeter')
registerNodeClass('watcher', 'TestWatch')
registerNodeClass('timedloop', 'TestLoop')
registerNodeClass('getdata', 'GetData')
registerNodeClass('intgen', 'IntGen')
