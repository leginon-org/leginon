class Node(object):
	def __init__(self, name):
		self.name = name
		self.bindingoutputs = []
		self.bindinginputs = []
		self.launcher = None
		self.application = None
		self.master = None

class Binding(object):
	def __init__(self, eventclass=None, fromnode=None, tonode=None):
		self.eventclass = eventclass
		self.fromnode = fromnode
		self.tonode = tonode
		self.application = None
		self.master = None

	def setFromNode(self, node):
		if self.fromnode is not None:
			self.fromnode.bindingoutputs.remove(self)
		self.fromnode = node
		if self.fromnode is not None:
			self.fromnode.bindingoutputs.append(self)

	def setToNode(self, node):
		if self.tonode is not None:
			self.tonode.bindinginputs.remove(self)
		self.tonode = node
		if self.tonode is not None:
			self.tonode.bindinginputs.append(self)

class Launcher(object):
	def __init__(self, name):
		self.name = name
		self.nodes = []
		self.application = None
		self.master = None

	def addNode(self, node):
		if node.launcher is not None:
			node.launcher.removeNode(node)
		if node not in self.nodes:
			self.nodes.append(node)
		else:
			raise ValueError('node already exists')
		node.launcher = self

	def removeNode(self, node):
		if node.launcher == self:
			node.launcher = None
		else:
			raise ValueError('node launcher attribute not self')
		if node in self.nodes:
			self.nodes.remove(node)
		else:
			raise ValueError('node does not exist')

class Application(object):
	def __init__(self, name):
		self.name = name
		self.nodes = []
		self.bindings = []
		self.launchers = []
		self.master = None

	def addNode(self, node):
		if node.application is not None:
			node.application.removeNode(node)
		if node not in self.nodes:
			self.nodes.append(node)
		else:
			raise ValueError('node already exists')
		node.application = self

	def removeNode(self, node):
		if node.application == self:
			node.application = None
		else:
			raise ValueError('node application attribute not self')
		if node in self.nodes:
			self.nodes.remove(node)
		else:
			raise ValueError('node does not exist')

	def addBinding(self, binding):
		if binding.application is not None:
			binding.application.removeBinding(binding)
		if binding not in self.bindings:
			self.bindings.append(binding)
		else:
			raise ValueError('binding already exists')
		binding.application = self

	def removeBinding(self, binding):
		if binding.application == self:
			binding.application = None
		else:
			raise ValueError('binding application attribute not self')
		if binding in self.bindings:
			self.bindings.remove(binding)
		else:
			raise ValueError('binding does not exist')

	def addLauncher(self, launcher):
		if launcher.application is not None:
			launcher.application.removeLauncher(launcher)
		if launcher not in self.launchers:
			self.launchers.append(launcher)
		else:
			raise ValueError('launcher already exists')
		launcher.application = self

	def removeLauncher(self, launcher):
		if launcher.application == self:
			launcher.application = None
		else:
			raise ValueError('launcher application attribute not self')
		if launcher in self.launchers:
			self.launchers.remove(launcher)
		else:
			raise ValueError('launcher does not exist')

class Master(object):
	def __init__(self):
		self.nodes = []
		self.bindings = []
		self.launchers = []
		self.applications = []

	def addNode(self, node):
		if node.master is not None:
			node.master.removeNode(node)
		if node not in self.nodes:
			self.nodes.append(node)
		else:
			raise ValueError('node already exists')
		node.master = self

	def removeNode(self, node):
		if node.master == self:
			node.master = None
		else:
			raise ValueError('node master attribute not self')
		if node in self.nodes:
			self.nodes.remove(node)
		else:
			raise ValueError('node does not exist')

	def addBinding(self, binding):
		if binding.master is not None:
			binding.master.removeBinding(binding)
		if binding not in self.bindings:
			self.bindings.append(binding)
		else:
			raise ValueError('binding already exists')
		binding.master = self

	def removeBinding(self, binding):
		if binding.master == self:
			binding.master = None
		else:
			raise ValueError('binding master attribute not self')
		if binding in self.bindings:
			self.bindings.remove(binding)
		else:
			raise ValueError('binding does not exist')

	def addLauncher(self, launcher):
		if launcher.master is not None:
			launcher.master.removeLauncher(launcher)
		if launcher not in self.launchers:
			self.launchers.append(launcher)
		else:
			raise ValueError('launcher already exists')
		launcher.master = self

	def removeLauncher(self, launcher):
		if launcher.master == self:
			launcher.master = None
		else:
			raise ValueError('launcher master attribute not self')
		if launcher in self.launchers:
			self.launchers.remove(launcher)
		else:
			raise ValueError('launcher does not exist')

	def addApplication(self, application):
		if application.master is not None:
			application.master.removeApplication(application)
		if application not in self.applications:
			self.applications.append(application)
		else:
			raise ValueError('application already exists')
		application.master = self

	def removeApplication(self, application):
		if application.master == self:
			application.master = None
		else:
			raise ValueError('application master attribute not self')
		if application in self.applications:
			self.applications.remove(application)
		else:
			raise ValueError('application does not exist')

if __name__ == '__main__':
	import time

	m = Master()
	a = Application('foo')
	l = Launcher('bar')
	b = Binding()
	n = Node('foobar')

	m.addApplication(a)
	m.addLauncher(l)
	a.addLauncher(l)
	m.addBinding(b)
	a.addBinding(b)
	m.addNode(n)
	a.addNode(n)
	l.addNode(n)
	b.setFromNode(n)
	b.setToNode(n)
	b.setToNode(None)
	b.setFromNode(None)
	l.removeNode(n)
	a.removeNode(n)
	m.removeNode(n)
	a.removeBinding(b)
	m.removeBinding(b)
	a.removeLauncher(l)
	m.removeLauncher(l)
	m.removeApplication(a)

	time.sleep(10.0)

