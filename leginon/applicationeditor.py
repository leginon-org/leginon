import Tkinter
import math
import application

class Line(object):
	def __init__(self, canvas, origin):
		self.canvas = canvas
		self.origin = origin
		self.destination = None
		self.line = None
		position = self.origin.getPosition()
		self.createline(position[0], position[1], position[0], position[1])

	def createline(self, x0, y0, x1, y1):
		self.line = self.canvas.create_line(x0, y0, x1, y1)
#		midpoint = (int(y1) + int(y0))/2
#		self.line1 = self.canvas.create_line(x0, y0, x0, midpoint)
#		self.line2 = self.canvas.create_line(x0, midpoint, x1, midpoint)
#		self.line3 = self.canvas.create_line(x1, midpoint, x1, y1)

	def move(self, x0, y0, x1, y1):
		self.canvas.coords(self.line, x0, y0, x1, y1)
#		midpoint = (int(y1) + int(y0))/2
#		self.canvas.coords(self.line1, x0, y0, x0, midpoint)
#		self.canvas.coords(self.line2, x0, midpoint, x1, midpoint)
#		self.canvas.coords(self.line3, x1, midpoint, x1, y1)

	def moveDestination(self, x, y):
		position = self.origin.getPosition()
		self.move(position[0], position[1], x, y)

	def moveToNodeLabel(self, destination):
		position = destination.getPosition()
		self.moveDestination(position[0], position[1])

	def connect(self, destination):
		self.destination = destination
		self.moveToNodeLabel(destination)

	def refresh(self):
		self.moveToNodeLabel(self.destination)

	def delete(self):
		self.canvas.delete(self.line)

class ArrowLine(Line):
	def createline(self, x0, y0, x1, y1):
		Line.createline(self, x0, y0, x1, y1)

	def move(self, x0, y0, x1, y1):
		Line.move(self, x0, y0, x1, y1)

class LabeledLine(ArrowLine):
	def __init__(self, canvas, originwidget, text):
		self.labeltext = text
		ArrowLine.__init__(self, canvas, originwidget)

	def createline(self, x0, y0, x1, y1):
		ArrowLine.createline(self, x0, y0, x1, y1)
		self.line = self.canvas.create_line(x0, y0, x1, y1)

		self.label = Tkinter.Label(self.canvas, text=self.labeltext,
																relief=Tkinter.RAISED, justify=Tkinter.LEFT,
																bd=1, padx=5, pady=3, bg='white')
		self.label.lower()
		self.label.place(x = (int(x1) + int(x0))/2, y = (int(y1) + int(y0))/2,
											anchor=Tkinter.CENTER)

	def move(self, x0, y0, x1, y1):
		ArrowLine.move(self, x0, y0, x1, y1)
		self.label.place(x = (int(x1) + int(x0))/2, y = (int(y1) + int(y0))/2,
											anchor=Tkinter.CENTER)

	def delete(self):
		ArrowLine.delete(self)
		self.label.place_forget()

class NodeLabel(object):
	def __init__(self, canvas, itext, editor):
		self.canvas = canvas
#		self.label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
#												justify=Tkinter.LEFT, bd=1, padx=5, pady=3, bg='white')
		self.text = self.canvas.create_text(100, 100, text=itext, justify=Tkinter.LEFT)
		self.box = self.canvas.create_rectangle(self.canvas.bbox(self.text))
#		self.label.bind('<Button-3>', self.abortConnection)
#		self.label.bind('<Motion>', self.moveConnection)
#		self.label.bind('<B1-Motion>', self.drag)
#		self.label.bind('<Button-1>', self.startDrag)
#		self.label.bind('<Double-Button-1>', self.handleConnection)
		self.lines = []
		self.editor = editor
		self.dragoffset = (0, 0)

	def getPosition(self):
#		info = self.label.place_info()
#		return (int(info['x']), int(info['y']))
		return self.canvas.coords(self.text)

	def move(self, x0, y0):
#		self.label.place(x = x0, y = y0, anchor=Tkinter.CENTER)

		coords = self.canvas.coords(self.box)
		offset = ((coords[2] - coords[0])/2, (coords[3] - coords[1])/2)
		self.canvas.coords(self.box, x0 - offset[0], y0 - offset[1],
																	x0 + offset[0], y0 + offset[1])
		self.canvas.coords(self.text, x0, y0)

		for i in range(len(self.lines)):
			self.lines[i].refresh()

	def moveConnection(self, ievent):
		if self.editor.activeconnection is not None:
			self.editor.activeconnection.moveToNodeLabel(self)

	def drag(self, ievent):
		self.abortConnection(ievent)
		position = self.getPosition()
		self.move(position[0] + ievent.x - self.dragoffset[0],
							position[1] + ievent.y - self.dragoffset[1])

	def startDrag(self, ievent):
		self.dragoffset = (ievent.x, ievent.y)

	def handleConnection(self, ievent):
		if self.editor.activeconnection is None:
			self.startConnection()
		else:
			self.finishConnection()

	def startConnection(self, text='<None>'):
		self.editor.activeconnection = LabeledLine(self.canvas, self, text)

	def finishConnection(self):
		self.editor.activeconnection.connect(self)
		self.lines.append(self.editor.activeconnection)
		self.editor.activeconnection.origin.lines.append(
																					self.editor.activeconnection)
		self.editor.activeconnection = None

	def abortConnection(self, ievent):
		if self.editor.activeconnection is not None:
			self.editor.activeconnection.delete()
			self.editor.activeconnection = None

class Editor(Tkinter.Frame):
	def __init__(self, parent, **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.pack(fill=Tkinter.BOTH, expand=1)
		self.nodes = []
		self.activeconnection = None
		self.canvas = Tkinter.Canvas(self, height=600, width=800, bg='white')
		self.canvas.bind('<Button-3>', self.abortConnection)
		self.canvas.bind('<Motion>', self.moveConnection)
		self.canvas.pack(fill=Tkinter.BOTH, expand=1)

	def moveConnection(self, ievent):
		if self.activeconnection is not None:
			self.activeconnection.moveDestination(ievent.x, ievent.y)

	def abortConnection(self, ievent):
		if self.activeconnection is not None:
			self.activeconnection.delete()
			self.activeconnection = None

	def addNode(self, text):
		node = NodeLabel(self.canvas, text, self)
		self.nodes.append(node)
		self.circle()
		return node

	def addConnection(self, origin, destination, text):
		origin.startConnection(text)
		destination.finishConnection()

	def circle(self):
		radius = 200
		center = (400, 300)
		angle = 2*math.pi/len(self.nodes)
		for i in range(len(self.nodes)):
			self.nodes[i].move(int(round(math.cos(i*angle)*radius + center[0])),
													int(round(math.sin(i*angle)*radius + center[1])))

class ApplicationEditor(Editor):
	def __init__(self, parent, **kwargs):
		Editor.__init__(self, parent, **kwargs)
		self.mapping = {}

	def load(self, filename):
		self.app = application.Application(('AE Application',), None)
		self.app.load(filename)
		for args in self.app.launchspec:
			self.displayNode(args)
		for binding in self.app.bindspec:
			self.displayConnection(binding)

	def displayNode(self, args):
		labelstring = \
					"Name: %s\nClass: %s\nLauncher: %s\nProcess: %s\nArgs: %s" \
														% (args[3], args[2], args[0], args[1], args[4])
		self.mapping[('manager', args[3])] = Editor.addNode(self, labelstring)

	def displayConnection(self, binding):
		self.addConnection(self.mapping[binding[1]], self.mapping[binding[2]],
																													str(binding[0]))
		

if __name__ == '__main__':
	import sys

	root = Tkinter.Tk()
	ae = ApplicationEditor(root)
	ae.load(sys.argv[1])
	ae.pack()
	root.mainloop()

