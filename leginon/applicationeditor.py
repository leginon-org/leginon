import Tkinter
import math
import application

class Line(object):
	def __init__(self, canvas, origin):
		self.canvas = canvas
		self.origin = origin
		self.destination = None
		self.line = None
		self.label = None
		self.createline(self.origininfo['x'], self.origininfo['y'],
										self.origininfo['x'], self.origininfo['y'])

	def createline(self, x0, y0, x1, y1, itext=None):
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
		position = self.origin.getPostiion()
		self.move(position[0], position[1], x, y)

	def moveToNodeLabel(self, destination):
		position = destination.getPostiion()
		self.moveDestination(position[0], position[1])

	def connect(self, destination):
		self.destination = destination
		self.moveToNodeLabel(destination)

	def refresh(self):
		self.moveToNodeLabel(self.destination)

	def delete(self):
		self.canvas.delete(self.line)

class LabeledLine(Line):
	def __init__(self, canvas, originwidget, text):
		self.labeltext = text
		Line.__init__(self, canvas, originwidget)

	def createline(self, x0, y0, x1, y1):
		Line.createline(self, x0, y0, x1, y1)
		self.line = self.canvas.create_line(x0, y0, x1, y1)

		self.label = Tkinter.Label(self.canvas, text=self.labeltext,
																relief=Tkinter.RAISED, justify=Tkinter.LEFT,
																bd=1, padx=5, pady=3, bg='white')
		self.label.lower()
		self.label.place(x = (int(x1) + int(x0))/2, y = (int(y1) + int(y0))/2,
											anchor=Tkinter.CENTER)

	def move(self, x0, y0, x1, y1):
		Line.move(self, x0, y0, x1, y1)
		self.label.place(x = (int(x1) + int(x0))/2, y = (int(y1) + int(y0))/2,
											anchor=Tkinter.CENTER)

	def delete(self):
		Line.delete(self)
		self.label.place_forget()

class NodeLabel(object):
	def __init__(self, canvas, itext, editor):
		self.canvas = canvas
		self.label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
												justify=Tkinter.LEFT, bd=1, padx=5, pady=3, bg='white')
		self.label.bind('<Button-3>', self.stopLine)
		self.label.bind('<Motion>', self.doLine)
		self.label.bind('<B1-Motion>', self.drag)
		self.label.bind('<Double-Button-1>', self.handleConnect)
		self.lines = []
		self.editor = editor

	def getPosition(self):
		info = self.label.place_info()
		return (int(info['x']), int(info['y']))

	def move(self, x0, y0):
		self.label.place(x = x0, y = y0, anchor=Tkinter.CENTER)
		for i in range(len(self.lines)):
			self.lines[i].refresh()

	def doLine(self, ievent):
		if self.editor.activeconnection is not None:
#			if not isinstance(ievent.widget, Tkinter.Label):
#				self.activeline.moveDestination(ievent.x, ievent.y)
#			else:
			self.activeline.moveDestinationWidget(self.label)

	def drag(self, ievent):
		self.stopLine(ievent)
		position = self.getPosition()
		self.move(position[0] + ievent.x, position[1] + ievent.y)

	def handleConnect(self, ievent):
		if self.editor.activeconnection is None:
			self.startConnection()
		else:
			self.completeConnection()

	def startConnection(self):
		self.activeline = LabeledLine(self.canvas, self, '<None>')

	def completeConnection(self):
		self.editor.activeconnection.connect(self)
		self.lines.append(self.editor.activeconnection)
		self.editor.activeconnection = None

	def stopLine(self, ievent):
		if self.editor.activeconnection is not None:
			self.editor.activeconnection.delete()
			self.editor.activeconnection = None

class Editor(Tkinter.Frame):
	def __init__(self, parent, **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.pack(fill=Tkinter.BOTH, expand=1)
		self.labels = []
		self.activeconnection = None
		self.canvas = Tkinter.Canvas(self)
		self.canvas.bind('<Button-3>', self.stopLine)
		self.canvas.bind('<Motion>', self.moveLine)
		self.canvas.pack(fill=Tkinter.BOTH, expand=1)

	def moveLine(self, ievent):
		if self.activeconnection is not None:
			self.activeconnection.moveDestination(ievent.x, ievent.y)

	def stopLine(self, ievent):
		if self.activeconnection is not None:
			self.activeconnection.delete()
			self.activeconnection = None

	def addNode(self, text):
		label = NodeLabel(self.canvas, text, self)
		self.labels.append(label)
		self.circle()
		return label

	def circle(self):
		radius = 50
		center = 100
		angle = 2*math.pi/len(self.labels)
		for i in range(len(self.labels)):
			self.labels[i].move(int(round(math.cos(i*angle)*radius + center)),
													int(round(math.sin(i*angle)*radius + center)))

class ApplicationEditor(Editor):
	def __init__(self, parent, **kwargs):
		Editor.__init__(self, parent, **kwargs)

	def load(self, filename):
		self.app = application.Application(('Application Editor Application',),
																				None)
		self.app.load(filename)
		mapping = {}
		for args in self.app.launchspec:
			labelstring = \
					"Name: %s\nClass: %s\nLauncher: %s\nProcess: %s\nArgs: %s\n" \
														% (args[3], args[2], args[0], args[1], args[4])
			mapping[('manager', args[3])] = self.addNode(labelstring)

		for binding in self.app.bindspec:
			mapping[binding[1]], mapping[binding[2]],
																										str(binding[0]))

if __name__ == '__main__':
	import sys

	root = Tkinter.Tk()
	ae = ApplicationEditor(root)
	ae.load(sys.argv[1])
	ae.pack()
	root.mainloop()

