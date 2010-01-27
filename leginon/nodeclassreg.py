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

def registerNodeClass(modulename, classname, sortclass=None, subpackage=''):
	import leginon
	leginonpath = leginon.__path__[0]
	if subpackage:
		packagepath = os.path.join(leginonpath, subpackage)
	else:
		packagepath = leginonpath
	### find the module
	try:
		modinfo = imp.find_module(modulename, [packagepath])
	except ImportError, detail:
		raise NotFoundError('module \'%s\' not found' % modulename)

	### import the module (if not already imported)
	if subpackage:
		impname = 'leginon' + '.' + subpackage + '.' + modulename
	else:
		impname = 'leginon' + '.' + modulename
	if impname in sys.modules:
		mod = sys.modules[impname]
	else:
		try:
				mod = imp.load_module(impname, *modinfo)
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
			subpackage = configparser.get(classname, 'package')
		except ConfigParser.NoOptionError:
			subpackage = ''
		registerNodeClass(modulename, classname, sortclass, subpackage)

registerNodeClasses()

