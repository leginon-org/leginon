class Node(object):
	def __init__(self, name):
		self.name = name

class Binding(object):
	def __init__(self, eventclass=None, fromnode=None, tonode=None):
		self.eventclass = eventclass
		self.fromnode = fromnode
		self.tonode = tonode

class Launcher(object):
	def __init__(self, name):
		self.name = name
		self.nodes = []

	def addNode(self, node):
		if node not in self.nodes:
			self.nodes.append(node)

	def removeNode(self, node):
		if node in self.nodes:
			self.nodes.remove(node)

class Application(object):
	def __init__(self, name):
		self.name = name
		self.nodes = []
		self.launchers = []

	def addNode(self, node):
		if node not in self.nodes:
			self.nodes.append(node)

	def removeNode(self, node):
		if node in self.nodes:
			self.nodes.remove(node)

	def addLauncher(self, launcher):
		if launcher not in self.lauchers:
			self.launchers.append(launcher)

	def removeLauncher(self, launcher):
		if launcher in self.launchers:
			self.launchers.remove(launcher)

class Master(object):
	def __init__(self):
		self.nodes = []
		self.launchers = []
		self.applications = []

	def addNode(self, node):
		if node not in self.nodes:
			self.nodes.append(node)

	def removeNode(self, node):
		if node in self.nodes:
			self.nodes.remove(node)

	def addLauncher(self, launcher):
		if launcher not in self.lauchers:
			self.launchers.append(launcher)

	def removeLauncher(self, launcher):
		if launcher in self.launchers:
			self.launchers.remove(launcher)

	def addApplication(self, application):
		if application not in self.applications:
			self.applications.append(application)

	def removeApplication(self, application):
		if application in self.applications:
			self.applications.remove(application)

