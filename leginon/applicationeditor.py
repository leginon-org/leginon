import Tkinter
import math
import application

class Line(object):
	def __init__(self, canvas, originwidget):
		self.canvas = canvas
		self.originwidget = originwidget
		self.origininfo = self.originwidget.place_info()
		self.destinationwidget = None
		self.destinationinfo = None
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
		self.move(self.origininfo['x'], self.origininfo['y'], x, y)

	def moveDestinationWidget(self, widget):
		info = widget.place_info()
		self.moveDestination(info['x'], info['y'])

	def connect(self, widget):
		self.destinationwidget = widget
		self.destinationinfo = self.destinationwidget.place_info()
		self.moveDestination(self.destinationinfo['x'], self.destinationinfo['y'])

	def refresh(self):
		self.origininfo = self.originwidget.place_info()
		# letting this fall through for now

	def moveDestination(self, x, y):
		self.move(self.origininfo['x'], self.origininfo['y'], x, y)

	def moveDestinationWidget(self, widget):
		info = widget.place_info()
		self.moveDestination(info['x'], info['y'])

	def connect(self, widget):
		self.destinationwidget = widget
		self.destinationinfo = self.destinationwidget.place_info()
		self.moveDestination(self.destinationinfo['x'], self.destinationinfo['y'])

	def refresh(self):
		self.origininfo = self.originwidget.place_info()
		# letting this fall through for now
		self.destinationinfo = self.destinationwidget.place_info()
		self.move(self.origininfo['x'], self.origininfo['y'],
							self.destinationinfo['x'], self.destinationinfo['y'])

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
	def __init__(self, canvas, itext):
		self.canvas = canvas
		self.label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
												justify=Tkinter.LEFT, bd=1, padx=5, pady=3, bg='white')
		self.label.bind('<Button-3>', self.stopLine)
		self.label.bind('<Motion>', self.doLine)
		self.label.bind('<B1-Motion>', self.drag)
		self.label.bind('<Double-Button-1>', self.handleConnect)
		self.activeconnection = None

	def move(self, x0, y0):
		lines = []
		for i in range(len(self.lines)):
			if self.lines[i].originwidget is widget or \
										self.lines[i].destinationwidget is widget:
				lines.append(self.lines[i])

		self.label.place(x=x0, y=y0, anchor=Tkinter.CENTER)

		for i in range(len(lines)):
			lines[i].refresh()

	def doLine(self, ievent):
		if self.activeconnection is not None:
#			if not isinstance(ievent.widget, Tkinter.Label):
#				self.activeline.moveDestination(ievent.x, ievent.y)
#			else:
			self.activeline.moveDestinationWidget(self.label)

	def drag(self, ievent):
		self.stopLine(ievent)
		info = self.label.place_info()
		self.move(int(info['x']) + ievent.x, int(info['y']) + ievent.y)

	def handleConnect(self, ievent):
		if self.activeline is None:
			self.startConnection()
		else:
			self.completeConnection(ievent.widget)

	def startConnection(self):
		self.activeline = LabeledLine(self.canvas, ievent.widget, '<None>')

	def completeConnection(self, widget):
		self.activeline.connect(ievent.widget)
		self.lines.append(self.activeline)
		self.activeline = None

	def stopLine(self, ievent):
		if self.activeline is not None:
			self.activeline.delete()
			self.activeline = None

class Editor(Tkinter.Frame):
	def __init__(self, parent, **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.pack(fill=Tkinter.BOTH, expand=1)
		self.labels = []
		self.lines = []
		self.activeline = None
		self.canvas = Tkinter.Canvas(self)
		self.canvas.bind('<Button-3>', self.undoLine)
		self.canvas.bind('<Motion>', self.doLine)
		self.canvas.pack(fill=Tkinter.BOTH, expand=1)

	def addConnection(self, originwidget, destinationwidget, text):
		line = LabeledLine(self.canvas, originwidget, text)
		line.connect(destinationwidget)
		self.lines.append(line)

	def doLine(self, ievent):
		if self.activeline is not None:
			if not isinstance(ievent.widget, Tkinter.Label):
				self.activeline.moveDestination(ievent.x, ievent.y)
			else:
				self.activeline.moveDestinationWidget(ievent.widget)

	def undoLine(self, ievent):
		if self.activeline is not None:
			self.activeline.delete()
			self.activeline = None

	def moveLabel(self, widget, x0, y0):
		lines = []
		for i in range(len(self.lines)):
			if self.lines[i].originwidget is widget or \
										self.lines[i].destinationwidget is widget:
				lines.append(self.lines[i])

		widget.place(x=x0, y=y0, anchor=Tkinter.CENTER)
		info = widget.place_info()

		for i in range(len(lines)):
			lines[i].refresh()

	def dragLabel(self, ievent):
		self.undoLine(ievent)
		info = ievent.widget.place_info()
		self.moveLabel(ievent.widget, int(info['x']) + ievent.x,
																	int(info['y']) + ievent.y)

	def addNode(self, itext):
		label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
																											bd=2, padx=5, pady=3)
		self.labels.append(label)
		self.circle()
		return label

	def circle(self):
		radius = 50
		center = 100
		angle = 2*math.pi/len(self.labels)
		for i in range(len(self.labels)):
			self.moveLabel(self.labels[i], 
											int(round(math.cos(i*angle)*radius + center)),
											int(round(math.sin(i*angle)*radius + center)))
			self.labels[i].bind('<Button-3>', self.undoLine)
			self.labels[i].bind('<Motion>', self.doLine)
			self.labels[i].bind('<B1-Motion>', self.dragLabel)
			self.labels[i].bind('<Double-Button-1>', self.handleConnect)

	def handleConnect(self, ievent):
		if self.activeline is None:
			self.activeline = LabeledLine(self.canvas, ievent.widget, '<None>')
		else:
			self.activeline.connect(ievent.widget)
			self.lines.append(self.activeline)
			self.activeline = None

	def doLine(self, ievent):
		if self.activeline is not None:
			if not isinstance(ievent.widget, Tkinter.Label):
				self.activeline.moveDestination(ievent.x, ievent.y)
			else:
				self.activeline.moveDestinationWidget(ievent.widget)

	def undoLine(self, ievent):
		if self.activeline is not None:
			self.activeline.delete()
			self.activeline = None

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
			self.addConnection(mapping[binding[1]], mapping[binding[2]],
																										str(binding[0]))

if __name__ == '__main__':
	import sys

	root = Tkinter.Tk()
	ae = ApplicationEditor(root)
	ae.load(sys.argv[1])
	ae.pack()
	root.mainloop()

