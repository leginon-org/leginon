from wxPython.wx import *
from wxPython.ogl import *

wxOGLInitialize()

class MasterMixIn(object):
	def __init__(self, master):
		self._setMaster(master)

	def setMaster(self, master):
		self._setMaster(master)

	def _setMaster(self, master):
		self.master = master

	def getMaster(self):
		return self.master

class ApplicationMixIn(object):
	def __init__(self, application=None):
		self.setApplication(application)

	def setApplication(self, application):
		self._setApplication(application)

	def _setApplication(self, application):
		self.application = application

	def getApplication(self):
		return self.application

class LauncherMixIn(object):
	def __init__(self, launcher=None):
		self._setLauncher(launcher)

	def _setLauncher(self, launcher):
		self.launcher = launcher

	def getLauncher(self):
		return self.launcher

class NodesMixIn(object):
	def __init__(self):
		self.nodes = []

	def _addNode(self, node):
		if node in self.nodes:
			raise ValueError('node already exists')
		self.nodes.append(node)

	def _deleteNode(self, node):
		if node not in self.nodes:
			raise ValueError('node does not exist')
		self.nodes.remove(node)

class LaunchersMixIn(object):
	def __init__(self):
		self.launchers = []

	def _addLauncher(self, launcher):
		if launcher in self.launchers:
			raise ValueError('launcher already exists')
		self.launchers.append(launcher)

	def _deleteLauncher(self, launcher):
		if launcher not in self.launchers:
			raise ValueError('launcher does not exist')
		self.launchers.remove(launcher)

class ApplicationsMixIn(object):
	def __init__(self):
		self.applications = []

	def _addApplication(self, application):
		if application in self.applications:
			raise ValueError('application already exists')
		self.applications.append(application)

	def _deleteApplication(self, application):
		if application not in self.applications:
			raise ValueError('application does not exist')
		self.applications.remove(application)

class Binding(MasterMixIn):
	def __init__(self, master, eventclass=None, fromnode=None, tonode=None):
		MasterMixIn.__init__(self, master)
		self._setEventClass(eventclass)
		self.fromnode = None
		self.tonode = None
		self.setFromNode(fromnode)
		self.setToNode(tonode)

	def setMaster(self, master):
		MasterMixIn.setMaster(self, master)

	def _setEventClass(self, eventclass):
		self.eventclass = eventclass

	def getEventClass(self):
		return self.eventclass

	def setFromNode(self, fromnode):
		if self.fromnode is not None:
			self.fromnode._deleteBindingOutput(self)
		self._setFromNode(fromnode)
		if self.fromnode is not None:
			self.fromnode._addBindingOutput(self)

	def _setFromNode(self, fromnode):
		self.fromnode = fromnode

	def getFromNode(self):
		return self.fromnode

	def setToNode(self, tonode):
		if self.tonode is not None:
			self.tonode._deleteBindingInput(self)
		self._setToNode(tonode)
		if self.tonode is not None:
			self.tonode._addBindingInput(self)

	def _setToNode(self, tonode):
		self.tonode = tonode

	def getToNode(self):
		return self.tonode

class Node(MasterMixIn, ApplicationMixIn, LauncherMixIn):
	def __init__(self, master, application=None, launcher=None, nodeclass=None):
		MasterMixIn.__init__(self, master)
		ApplicationMixIn.__init__(self, application)
		LauncherMixIn.__init__(self, launcher)
		self._setNodeClass(nodeclass)
		# not implemented
#		self.eventoutputs = []
#		self.eventinputs = []
		self.bindingoutputs = []
		self.bindinginputs = []

	def setMaster(self, master):
		MasterMixIn.setMaster(self, master)
		self.master._addNode(self)

	def setApplication(self, application):
		if self.application is not None:
			self.application._deleteNode(self)
		ApplicationMixIn.setApplication(self, application)
		if self.application is not None:
			self.application._addNode(self)

	def _setNodeClass(self):
		self.nodeclass = nodeclass

	def getNodeClass(self):
		return self.nodeclass

	def _addBindingInput(self, binding):
		if binding in self.bindinginputs:
			raise ValueError('binding input already exists')
		self.bindinginputs.append(binding)

	def _deleteBindingInput(self, binding):
		if binding not in self.bindinginputs:
			raise ValueError('binding input does not exist')
		self.bindinginputs.remove(binding)

	def _addBindingOutput(self, binding):
		if binding in self.bindingoutputs:
			raise ValueError('binding output already exists')
		self.bindingoutputs.append(binding)

	def _deleteBindingOutput(self, binding):
		if binding not in self.bindingoutputs:
			raise ValueError('binding output does not exist')
		self.bindingoutputs.remove(binding)

	def setLauncher(self, launcher):
		if self.launcher is not None:
			self.launcher._deleteNode(self)
		self._setLauncher(launcher)
		if self.launcher is not None:
			self.launcher._addNode(self)

	def setApplication(self, application):
		if self.application is not None:
			self.application._deleteNode(self)
		self._setApplication(application)
		if self.application is not None:
			self.application._addNode(self)

class Launcher(MasterMixIn, ApplicationMixIn, NodesMixIn):
	def __init__(self, master, application=None):
		MasterMixIn.__init__(self, master)
		ApplicationMixIn.__init__(self, application)
		NodesMixIn.__init__(self)

	def setMaster(self, master):
		MasterMixIn.setMaster(self, master)
		self.master._addLauncher(self)

	def setApplication(self, application):
		if self.application is not None:
			self.application._deleteLauncher(self)
		ApplicationMixIn.setApplication(self, application)
		if self.application is not None:
			self.application._addLauncher(self)

	def setApplication(self, application):
		if self.application is not None:
			self.application._deleteLauncher(self)
		self._setApplication(application)
		if self.application is not None:
			self.application._addLauncher(self)

class Application(MasterMixIn, NodesMixIn, LaunchersMixIn):
	def __init__(self, master, name):
		self.name = name
		MasterMixIn.__init__(self, master)
		NodesMixIn.__init__(self)
		LaunchersMixIn.__init__(self)

	def getName(self):
		return self.name

	def setMaster(self, master):
		MasterMixIn.setMaster(self, master)
		self.master._addApplication(self)

		# not implemented
#		self.eventoutputs = []
#		self.eventinputs = []
#		self.bindingoutputs = []
#		self.bindinginputs = []

class Master(NodesMixIn, LaunchersMixIn, ApplicationsMixIn):
	def __init__(self):
		NodesMixIn.__init__(self)
		LaunchersMixIn.__init__(self)
		ApplicationsMixIn.__init__(self)

		# not implemented
#		self.bindings = []

class wxApplication(wxRectangleShape):
	def __init__(self, application):
		self.application = application
		wxRectangleShape.__init__(self, 100, 50)

class wxMaster(wxShapeCanvas):
	def __init__(self, parent, frame):
		wxShapeCanvas.__init__(self, parent)
		self.master = Master()
		self.frame = frame
		self.SetBackgroundColour(wxWHITE)
		self.diagram = wxDiagram()
		self.SetDiagram(self.diagram)
		self.diagram.SetCanvas(self)
		self.shapes = []

#		dc = wxClientDC(self)
#		self.PrepareDC(dc)
#		for x in range(len(self.shapes)):
#			fromShape = self.shapes[x]
#			if x+1 == len(self.shapes):
#				toShape = self.shapes[0]
#			else:
#				toShape = self.shapes[x+1]
#			line = wxLineShape()
#			line.SetCanvas(self)
#			line.SetPen(wxBLACK_PEN)
#			line.SetBrush(wxBLACK_BRUSH)
#			line.AddArrow(ARROW_ARROW)
#			line.MakeLineControlPoints(2)
#			fromShape.AddLine(line, toShape)
#			self.diagram.AddShape(line)
#			line.Show(True)
#			line.Select()
#
#			# for some reason, the shapes have to be moved for the line to show up...
#			fromShape.Move(dc, fromShape.GetX(), fromShape.GetY())

	def addApplication(self, application):
		self.MasterAddShape(application, 100, 100, wxBLACK_PEN, wxWHITE_BRUSH, application.application.getName())

	def MasterAddShape(self, shape, x, y, pen, brush, text):
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

#		evthandler = MyEvtHandler(self.log, self.frame)
#		evthandler.SetShape(shape)
#		evthandler.SetPreviousHandler(shape.GetEventHandler())
#		shape.SetEventHandler(evthandler)

		self.shapes.append(shape)
		return shape

if __name__ == '__main__':
	class MyApp(wxApp):
		def OnInit(self):
			frame = wxFrame(NULL, -1, 'Nodes')
			self.SetTopWindow(frame)
			self.master = wxMaster(frame, frame) #TargetImagePanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.master.addApplication(wxApplication(Application(app.master, 'App 1')))
	app.MainLoop()

