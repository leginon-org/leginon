import Tkinter
import math
import application

class Line(object):
	def __init__(self, canvas, position1, position2):
		self.canvas = canvas
		self.createline(position1, position2)

	def createline(self, position1, position2):
		self.line = self.canvas.create_line(position1[0], position1[1],
																				position2[0], position2[1])
#		midpoint = (int(y1) + int(y0))/2
#		self.line1 = self.canvas.create_line(x0, y0, x0, midpoint)
#		self.line2 = self.canvas.create_line(x0, midpoint, x1, midpoint)
#		self.line3 = self.canvas.create_line(x1, midpoint, x1, y1)

	def move(self, position1, position2):
		self.canvas.coords(self.line, position1[0], position1[1],
																	position2[0], position2[1])
#		midpoint = (int(y1) + int(y0))/2
#		self.canvas.coords(self.line1, x0, y0, x0, midpoint)
#		self.canvas.coords(self.line2, x0, midpoint, x1, midpoint)
#		self.canvas.coords(self.line3, x1, midpoint, x1, y1)

	def delete(self):
		self.canvas.delete(self.line)

class ArrowLine(Line):
	def createline(self, originposition, destinationposition):
		Line.createline(self, originposition, destinationposition)

	def move(self, originposition, destinationposition):
		Line.move(self, originposition, destinationposition)

class LabeledLine(ArrowLine):
	def __init__(self, canvas, originposition, destinationposition, text):
		self.text = text
		ArrowLine.__init__(self, canvas, originposition, destinationposition)

	def createline(self, originposition, destinationposition):
		ArrowLine.createline(self, originposition, destinationposition)

		self.labeltext = Tkinter.StringVar()
		self.labeltext.set(self.text)
		self.label = Tkinter.Label(self.canvas, textvariable=self.labeltext,
																relief=Tkinter.RAISED, justify=Tkinter.LEFT,
																bd=1, padx=5, pady=3, bg='white')
		self.label.lower()
		self.label.place(
							x = (int(destinationposition[0]) + int(originposition[0]))/2,
							y = (int(destinationposition[1]) + int(originposition[1]))/2,
							anchor=Tkinter.CENTER)

	def move(self, originposition, destinationposition):
		ArrowLine.move(self, originposition, destinationposition)
		self.label.place(
							x = (int(destinationposition[0]) + int(originposition[0]))/2,
							y = (int(destinationposition[1]) + int(originposition[1]))/2,
							anchor=Tkinter.CENTER)

	def delete(self):
		ArrowLine.delete(self)
		self.label.place_forget()

	def append(self, itext):
		otext = self.labeltext.get()
		self.labeltext.set(otext + '\n' + itext)

class ConnectionManager(Line):
	def __init__(self, canvas):
		self.canvas = canvas
		self.activeconnection = None
		self.lines = {}

	def setActiveConnectionPosition(self, destination):
		if self.activeconnection is not None:
			originposition = self.activeconnection['origin'].getPosition()
			destinationposition = destination.getPosition()
			self.activeconnection['line'].move(originposition, destinationposition)

	def setActiveConnectionPositionRaw(self, position):
		originposition = self.activeconnection['origin'].getPosition()
		self.activeconnection['line'].move(originposition, position)

	def offsetPosition(self, origin, destination):
		originposition = origin.getPosition()
		destinationposition = destination.getPosition()
		if self.lines[(origin, destination)]['offset']:
			offset = 10
			angle = math.atan2(float(destinationposition[1] - originposition[1]),
												float(destinationposition[0] - originposition[0]))
			newangle = math.pi/2 + angle
			offsetvector = (math.cos(newangle)*offset, math.sin(newangle)*offset)
			return ((originposition[0] + offsetvector[0],
								originposition[1] + offsetvector[1]),
							(destinationposition[0] + offsetvector[0],
								destinationposition[1] + offsetvector[1]))
		else:
			return ((originposition[0], originposition[1]),
							(destinationposition[0], destinationposition[1]))

	def addConnection(self, origin, destination, text):
		key = (origin, destination)
		if key in self.lines:
			self.lines[key]['line'].append(text)
		else:
			self.lines[key] = {}
			inversekey = (destination, origin)
			if inversekey in self.lines:
				self.lines[key]['offset'] = True
				self.lines[inversekey]['offset'] = True
				position = self.offsetPosition(destination, origin)
				self.lines[inversekey]['line'].move(position[0], position[1])
			else:
				self.lines[key]['offset'] = False

			position = self.offsetPosition(origin, destination)
			self.lines[key]['line'] = LabeledLine(self.canvas, position[0],
																						position[1], text)

	def refreshConnections(self, widget):
		for key in self.lines:
			if key[0] == widget or key[1] == widget:
				position = self.offsetPosition(key[0], key[1])
				self.lines[key]['line'].move(position[0], position[1])

	def startConnection(self, origin, text='<None>'):
		if self.activeconnection is None:
			position = origin.getPosition()
			self.activeconnection = {}
			self.activeconnection['origin'] = origin
			self.activeconnection['text'] = text
			self.activeconnection['line'] = LabeledLine(self.canvas, position,
																													position, text)

	def finishConnection(self, destination):
		if self.activeconnection is not None:
			self.activeconnection['line'].delete()
			self.addConnection(self.activeconnection['origin'], destination,
																					self.activeconnection['text'])
			self.activeconnection = None

	def abortConnection(self, ievent=None):
		if self.activeconnection is not None:
			self.activeconnection['line'].delete()
			self.activeconnection = None

class NodeLabel(object):
	def __init__(self, canvas, itext, editor):
		self.canvas = canvas
		self.label = Tkinter.Label(self.canvas, text=itext, relief=Tkinter.RAISED,
												justify=Tkinter.LEFT, bd=1, padx=5, pady=3, bg='white')
		print self.label.winfo_reqheight()
		print self.label.winfo_reqwidth()
		self.editor = editor
		self.label.bind('<Button-3>', self.editor.connectionmanager.abortConnection)
		self.label.bind('<Motion>', self.moveConnection)
		self.label.bind('<B1-Motion>', self.drag)
		self.label.bind('<Button-1>', self.startDrag)
		self.label.bind('<Double-Button-1>', self.handleConnection)

	def getPosition(self):
		info = self.label.place_info()
		return (int(info['x']), int(info['y']))

	def move(self, x0, y0):
		self.label.place(x = x0, y = y0, anchor=Tkinter.CENTER)
		self.editor.connectionmanager.refreshConnections(self)

	def moveConnection(self, ievent):
		if self.editor.connectionmanager.activeconnection is not None:
			self.editor.connectionmanager.setActiveConnectionPosition(self)

	def drag(self, ievent):
		self.editor.connectionmanager.abortConnection()
		position = self.getPosition()
		self.move(position[0] + ievent.x - self.dragoffset[0],
							position[1] + ievent.y - self.dragoffset[1])

	def startDrag(self, ievent):
		self.dragoffset = (ievent.x, ievent.y)

	def handleConnection(self, ievent):
		if self.editor.connectionmanager.activeconnection is None:
			self.editor.connectionmanager.startConnection(self)
		else:
			self.editor.connectionmanager.finishConnection(self)

class Editor(Tkinter.Frame):
	def __init__(self, parent, **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.pack(fill=Tkinter.BOTH, expand=1)
		self.nodes = []
		self.canvas = Tkinter.Canvas(self, height=600, width=800, bg='white')
		self.connectionmanager = ConnectionManager(self.canvas)
		self.canvas.bind('<Button-3>', self.connectionmanager.abortConnection)
		self.canvas.bind('<Motion>', self.moveConnection)
		self.canvas.pack(fill=Tkinter.BOTH, expand=1)

	def moveConnection(self, ievent):
		if self.connectionmanager.activeconnection is not None:
			self.connectionmanager.setActiveConnectionPositionRaw((ievent.x,ievent.y))

	def addNode(self, text):
		node = NodeLabel(self.canvas, text, self)
		self.nodes.append(node)
		self.circle()
		return node

	def circle(self):
		radius = (250, 200)
		center = (400, 300)
		angle = 2*math.pi/len(self.nodes)
		for i in range(len(self.nodes)):
			self.nodes[i].move(int(round(math.cos(i*angle)*radius[0] + center[0])),
													int(round(math.sin(i*angle)*radius[1] + center[1])))

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
		self.connectionmanager.addConnection(self.mapping[binding[1]],
																					self.mapping[binding[2]],
																					str(binding[0]))

if __name__ == '__main__':
	import sys

	root = Tkinter.Tk()
	ae = ApplicationEditor(root)
	ae.load(sys.argv[1])
	ae.pack()
	root.mainloop()

