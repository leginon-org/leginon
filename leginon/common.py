
### this module is used as a container for all node classes

import node

from watcher import TestWatch
from timedloop import TestLoop
from acquireloop import AcquireLoop
from mynode import MyNode
from intgen import IntGen
from EM import EM
from emtest import EMTest
try:
	from imviewer2 import ImViewer
except ImportError:
	pass
from getdata import GetData

def nodeClasses():
	"""
	returns a dict:   {name: class_object, ...}
	that contains all the Node subclasses defined in this module
	"""

	nodeclasses = {}
	all_attrs = globals()
	for name,value in all_attrs.items():
		if type(value) == type:
			if issubclass(value, node.Node):
				nodeclasses[name] = value
	return nodeclasses
