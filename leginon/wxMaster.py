from wxPython.wx import *
from wxPython.ogl import *

class Node(wxRectangleShape):
	def __init__(self, name):
		self.name = name
		self.bindingoutputs = []
		self.bindinginputs = []
		self.launcher = None
		self.application = None
		self.master = None

		wxRectangleShape.__init__(self, 50, 50)

class Binding(object):
	def __init__(self, name, fromnode=None, tonode=None):
		self.name = name
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

class Launcher(wxRectangleShape):
	def __init__(self, name):
		self.name = name
		self.nodes = []
		self.application = None
		self.master = None

		wxRectangleShape.__init__(self, 100, 100)

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

class Application(wxRectangleShape):
	def __init__(self, name):
		self.name = name
		self.nodes = []
		self.bindings = []
		self.launchers = []
		self.master = None

		wxRectangleShape.__init__(self, 200, 200)

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

class Master(wxShapeCanvas):
	def __init__(self, parent):
		self.nodes = []
		self.bindings = []
		self.launchers = []
		self.applications = []

		wxShapeCanvas.__init__(self, parent)
		self.SetBackgroundColour(wxWHITE)
		self.diagram = wxDiagram()
		self.SetDiagram(self.diagram)
		self.diagram.SetCanvas(self)

	def addShape(self, shape):
		x = 100
		y = 100
		pen = wxBLACK_PEN
		brush = wxBrush(wxWHITE, wxTRANSPARENT) #wxWHITE_BRUSH
		text = shape.name
		shape.SetDraggable(True, True)
		shape.SetCanvas(self)
		shape.SetX(x)
		shape.SetY(y)
		if pen:
			shape.SetPen(pen)
		if brush:
			shape.SetBrush(brush)
		if text:
			shape.AddText(text)
		#shape.SetShadowMode(SHADOW_RIGHT)
		self.diagram.AddShape(shape)
		shape.Show(True)

	def removeShape(self, shape):
		shape.Destroy()

	def addNode(self, node):
		if node.master is not None:
			node.master.removeNode(node)
		if node not in self.nodes:
			self.nodes.append(node)
		else:
			raise ValueError('node already exists')
		node.master = self

		self.addShape(node)

	def removeNode(self, node):
		if node.master == self:
			node.master = None
		else:
			raise ValueError('node master attribute not self')
		if node in self.nodes:
			self.nodes.remove(node)
		else:
			raise ValueError('node does not exist')

		self.removeShape(node)

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

		self.addShape(launcher)

	def removeLauncher(self, launcher):
		if launcher.master == self:
			launcher.master = None
		else:
			raise ValueError('launcher master attribute not self')
		if launcher in self.launchers:
			self.launchers.remove(launcher)
		else:
			raise ValueError('launcher does not exist')

		self.removeShape(launcher)

	def addApplication(self, application):
		if application.master is not None:
			application.master.removeApplication(application)
		if application not in self.applications:
			self.applications.append(application)
		else:
			raise ValueError('application already exists')
		application.master = self

		self.addShape(application)

	def removeApplication(self, application):
		if application.master == self:
			application.master = None
		else:
			raise ValueError('application master attribute not self')
		if application in self.applications:
			self.applications.remove(application)
		else:
			raise ValueError('application does not exist')

		self.removeShape(application)

if __name__ == '__main__':
	import time

	class TestApp(wxApp):
		def OnInit(self):
			self.frame = wxFrame(NULL, -1, 'Image Viewer')
			self.SetTopWindow(self.frame)
			self.panel = wxPanel(self.frame, -1)
			self.frame.Fit()
			self.frame.Show(true)
			return true

	app = TestApp(0)
	m = Master(app.panel)
	m.SetSize((800, 800))
	app.panel.Fit()
	app.frame.Fit()

	a = Application('foo')
	l = Launcher('bar')
	b = Binding('bar None')
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
#	m.removeNode(n)
	a.removeBinding(b)
#	m.removeBinding(b)
	a.removeLauncher(l)
#	m.removeLauncher(l)
#	m.removeApplication(a)

	app.MainLoop()

