import leginon.node
import pyami.ordereddict

reg_dict = pyami.ordereddict.OrderedDict()

class NodeRegistryError(Exception):
	pass

class NotFoundError(NodeRegistryError):
	pass

class InvalidNodeError(NodeRegistryError):
	pass

def registerNodeClass(cls,classtype='Utility'):
	### make sure class is Node
	if not issubclass(cls, leginon.node.Node):
		raise InvalidNodeError('%s is not subclass of leginon.node.Node' % cls)

	### record this in the registry
	classname = cls.__name__
	cls.classtype = classtype
	reg_dict[classname] = cls

def getNodeClass(classname):
	if classname not in reg_dict:
		raise NotFoundError('\'%s\' not in registry' % classname)
	return reg_dict[classname]

def getNodeClassNames():
	return reg_dict.keys()

import leginon.allnodes
