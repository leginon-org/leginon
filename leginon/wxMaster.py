from wxPython.wx import *
from wxPython.ogl import *

wxOGLInitialize()

class MasterMixIn(object):
	def __init__(self, master):
		self._setMaster(master)

	def _setMaster(self, master):
		self.master = master

	def getMaster(self):
		return self.master

class ApplicationMixIn(object):
	def __init__(self, application=None):
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

	def addNode(self, node):
		self._addNode(node):

	def _addNode(self, node):
		if node in self.nodes:
			raise ValueError('node does already exists')
		self.nodes.append(node)

	def deleteNode(self, node):
		self._deleteNode(node)

	def _deleteNode(self, node):
		if node not in self.nodes:
			raise ValueError('node does not exist')
		self.nodes.remove(node)

class Binding(MasterMixIn):
	def __init__(self, master, eventclass=None, fromnode=None, tonode=None):
		MasterMixIn.__init__(self, master)
		self._setEventClass(eventclass)
		self.fromnode = None
		self.tonode = None
		self.setFromNode(fromnode)
		self.setToNode(tonode)

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

	def _setNodeClass(self):
		self.nodeclass = nodeclass

	def getNodeClass(self):
		return self.nodeclass

	def addBindingInput(self, binding):
		tonode = binding.getToNode()
		if tonode is not None:
			tonode._deleteBindingInput()
		binding._setToNode(self)
		self._addBindingInput(binding)

	def _addBindingInput(self, binding):
		if binding in self.bindinginputs:
			raise ValueError('binding input already exists')
		self.bindinginputs.append(binding)

	def deleteBindingInput(self, binding):
		binding._setToNode(None)
		self._deleteBindingInput(binding)

	def _deleteBindingInput(self, binding):
		if binding not in self.bindinginputs:
			raise ValueError('binding input does not exist')
		self.bindinginputs.remove(binding)

	def addBindingOutput(self, binding):
		fromnode = binding.getFromNode()
		if fromnode is not None:
			fromnode._deleteBindingOutput()
		binding._setFromNode(self)
		self._addBindingOutput(binding)

	def _addBindingOutput(self, binding):
		if binding in self.bindingoutputs:
			raise ValueError('binding output already exists')
		self.bindingoutputs.append(binding)

	def deleteBindingOutput(self, binding):
		binding._setFromNode(None)
		self._deleteBindingOutput(binding)

	def _deleteBindingOutput(self, binding):
		if binding not in self.bindingoutputs:
			raise ValueError('binding output does not exist')
		self.bindingoutputs.remove(binding)

class Launcher(MasterMixIn, ApplicationMixIn, NodesMixIn):
	def __init__(self, master, application=None):
		MasterMixIn.__init__(self, master)
		ApplicationMixIn.__init__(self, application)
		NodesMixIn.__init__(self)

	def addNode(self):

	def deleteNode(self):

class Application(MasterMixIn):
	def __init__(self, master):
		MasterMixIn.__init__(self, master)
		self.launchers = []
		self.nodes = []
		# not implemented
#		self.eventoutputs = []
#		self.eventinputs = []
#		self.bindingoutputs = []
#		self.bindinginputs = []

class Master(object):
	def __init__(self):
		self.applications = []
		self.launchers = []
		self.nodes = []
		self.bindings = []

class RectangleLineShape(wxLineShape):
	pass

class MyShapeCanvas(wxShapeCanvas):
	def __init__(self, parent, frame):
		wxShapeCanvas.__init__(self, parent)
		self.frame = frame
		self.SetBackgroundColour(wxWHITE)
		self.diagram = wxDiagram()
		self.SetDiagram(self.diagram)
		self.diagram.SetCanvas(self)
		self.shapes = []

		self.MyAddShape(wxRectangleShape(100, 50), 100, 250,
										wxBLACK_PEN, wxWHITE_BRUSH, "Rectangle")
		self.MyAddShape(wxRectangleShape(100, 50), 500, 250,
										wxBLACK_PEN, wxWHITE_BRUSH, "Rectangle")
		self.MyAddShape(wxRectangleShape(100, 50), 100, 500,
										wxBLACK_PEN, wxWHITE_BRUSH, "Rectangle")

		dc = wxClientDC(self)
		self.PrepareDC(dc)
		for x in range(len(self.shapes)):
			fromShape = self.shapes[x]
			if x+1 == len(self.shapes):
				toShape = self.shapes[0]
			else:
				toShape = self.shapes[x+1]
			line = wxLineShape()
			line.SetCanvas(self)
			line.SetPen(wxBLACK_PEN)
			line.SetBrush(wxBLACK_BRUSH)
			line.AddArrow(ARROW_ARROW)
			line.MakeLineControlPoints(2)
			fromShape.AddLine(line, toShape)
			self.diagram.AddShape(line)
			line.Show(True)
			line.Select()

			# for some reason, the shapes have to be moved for the line to show up...
			fromShape.Move(dc, fromShape.GetX(), fromShape.GetY())

	def MyAddShape(self, shape, x, y, pen, brush, text):
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
			self.panel = MyShapeCanvas(frame, frame) #TargetImagePanel(frame, -1)
			frame.Fit()
			frame.Show(true)
			return true

	app = MyApp(0)
	app.MainLoop()

