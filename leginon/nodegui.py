#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface
# why doesn't this work? add <python dir>\Tools\idle to your PYTHONPATH
import TreeWidget
import os
import threading
import socket
from ImageViewer import ImageViewer
import Mrc
import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib
from timer import Timer
import xmlrpcserver
import newtree

False=0
True=1

class SpecWidget(Frame):
	def __init__(self, parent, uiclient, spec,
											styled=True, server=False, **kwargs):
		Frame.__init__(self, parent, **kwargs)
		self.parent = parent
		self.spec = spec
		self.id = self.spec['id']
		self.uiclient = uiclient
		self.styled = styled
		if self.styled:
			self['bg'] = '#4488BB'
			self.buttoncolor = '#7AA6C5'
			self.entrycolor = '#FFF'
		self.server = server

	def refresh(self, spec):
		self.spec = spec

class Container(SpecWidget):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		SpecWidget.__init__(self, parent, uiclient, spec, styled, server)
		if self.styled:
			self.label = Label(self, text=spec['name'], bg=self['bg'])
		else:
			self.label = Label(self, text=spec['name'])
		self.label.pack()
		self.name = spec['name']
		self.build()

	def build(self):
		content = self.spec['content']
		self.content = {}
		for spec in content:
			id = spec['id']
			w = widgetFromSpec(self, self.uiclient, spec, self.styled, self.server)
			if w.__class__ is TreeData:
				w.pack(side=TOP, expand=YES, fill=BOTH)
			else:
				w.pack(side=TOP)
			self.content[id] = w

	def refresh(self, spec):
		SpecWidget.refresh(self, spec)
		for cspec in spec['content']:
			id = cspec['id']
			self.content[id].refresh(cspec)

	def getWidgetInstance(self, widgetid):
		containers = []
		for id in self.content:
			if widgetid == id:
				return self.content[id]
			if isinstance(self.content[id], Container):
				containers.append(self.content[id])
		for container in containers:
			instance = container.getWidgetInstance(widgetid)
			if instance is not None:
				return instance
		return None

class NotebookContainer(Container):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Container.__init__(self, parent, uiclient, spec, styled, server)

	def build(self):
		self.notebook = Pmw.NoteBook(self)
		content = self.spec['content']
		self.content = {}
		total_tab_width = 0
		for spec in content:
			name = spec['name']
			id = spec['id']
			newframe = self.notebook.add(name)
			tabwidth = self.tabwidth(name)
			total_tab_width += tabwidth

			w = widgetFromSpec(newframe, self.uiclient, spec,
																self.styled, self.server)
			if w.__class__ is TreeData:
				w.pack(expand=YES, fill=BOTH)
			else:
				w.pack()
			self.content[id] = w
		self.notebook.pack(fill=BOTH, expand=YES)
		self.notebook.setnaturalsize()
		self.notebook.component('hull')['width'] = total_tab_width

	def tabwidth(self, name):
		tabname = name + '-tab'
		w = self.notebook.component(tabname).winfo_reqwidth()
		return w

def widgetFromSpec(parent, uiclient, spec, styled=True, server=False):
	spectype = spec['spectype']
	if spectype == 'container':
		widget = Container(parent, uiclient, spec, styled, server)
	elif spectype == 'method':
		widget = Method(parent, uiclient, spec, styled, server)
	elif spectype == 'data':
		dataclass = whichDataClass(spec)
		widget = dataclass(parent, uiclient, spec, styled, server)
	else:
		raise RuntimeError('invalid spec type')
	return widget

def whichDataClass(dataspec):
	'''this checks a data spec to figure out what Data class to use'''
	type = dataspec['xmlrpctype']
	if 'choices' in dataspec:
		choices = dataspec['choices']
		choicesid = choices['id']
		choicestype  = choices['type']
	else:
		choices = None

	if choices is not None:
		if choicestype == 'array':
			return ComboboxData
		elif choicestype == 'struct':
			return TreeSelectorData
			## could probably make this an option too if it works
			## return DependentComboboxData
		else:
			raise RuntimeError('choices type %s not supported' % choicestype)
	elif type == 'boolean':
		return CheckbuttonData
	elif type in ('integer', 'float', 'string', 'array'):
		return EntryData
	elif type == 'struct':
		return TreeData
	elif type == 'binary':
		return ImageData
	else:
		raise RuntimeError('type not supported')

class Data(SpecWidget):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		if styled:
			SpecWidget.__init__(self, parent, uiclient, spec,
													styled, server, bd=2, relief=SOLID)
		else:
			SpecWidget.__init__(self, parent, uiclient, spec, styled, server)
		self.getbutton = None
		self.setbutton = None
		self.initInfo(spec)
		self.build()
	
	def initInfo(self, spec):
		self.name = spec['name']
		self.type = spec['xmlrpctype']
		if 'choices' in spec:
			self.choices = spec['choices']
			self.choicesid = self.choices['id']
			self.choicestype = self.choices['type']
		else:
			self.choices = None
		if 'permissions' in spec:
			self.permissions = spec['permissions']
		else:
			self.permissions = None
		if 'python name' in spec:
			self.pyname = spec['python name']
		else:
			self.pyname = None

#		if 'default' in spec:
#			self.default = spec['default']
#		else:
#			self.default = None

	def build(self):
		headframe = Frame(self)

		### label
		if self.styled:
			self.label = Label(headframe, text=self.name, bg=self['bg'])
			self.label.pack(side=LEFT, fill=BOTH)
		else:
			self.label = Label(headframe, text=self.name)
			self.label.grid(row = 0, column = 0)
#		self.label.pack(side=LEFT, fill=BOTH)

		### optional get/set
		if self.permissions is not None:
			if 'r' in self.permissions and not self.server:
				if self.styled:
					self.getbutton = Button(headframe, text='Get',
																	command=self.getServer, bg=self.buttoncolor)
					self.getbutton.pack(side=RIGHT)
				else:
					self.getbutton = Button(headframe, text='Get', command=self.getServer)
					self.getbutton.grid(row = 0, column = 1)
			if 'w' in self.permissions:
				if self.styled:
					self.setbutton = Button(headframe, text='Set',
																	command=self.setServer, bg=self.buttoncolor)
					self.setbutton.pack(side=RIGHT)
				else:
					self.setbutton = Button(headframe, text='Set', command=self.setServer)
					self.setbutton.grid(row = 0, column = 2)

		if self.styled:
			headframe.pack(side=TOP)
		else:
			headframe.grid(row = 0, column = 0)

		### the actual data widget
		if self.styled:
			w = self.buildWidget(self)
		else:
			w = self.buildWidget(headframe)

#		if self.default is not None and self.default:
#			self.getServer()

		self.getServer()

		if self.styled:
			w.pack(side=TOP, expand=YES, fill=BOTH)
		else:
			w.grid(row = 1, column = 0, columnspan = 3)

	def refresh(self, spec):
		SpecWidget.refresh(self, spec)
		self.initInfo(spec)
#		if self.default is not None and self.default:
#			self.getServer()
		self.getServer()

	def setServer(self):
		value = self.getWidget()
		r = self.uiclient.execute('SET', (self.id, value))
		self.setWidget(r)

	def getServer(self):
		r = self.uiclient.execute('GET', (self.id,))
		self.setWidget(r)

	def buildWidget(self, parent):
		'''implementation should return a data widget'''
		raise NotImplementedError()

	def setWidget(self, value):
		raise NotImplementedError()

	def getWidget(self):
		raise NotImplementedError()


class EntryData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)

	def buildWidget(self, parent):
		if self.styled:
			self.entry = Entry(parent, width=10, bg=self.entrycolor)
		else:
			self.entry = Entry(parent, width=10)
		self.entry.bind('<KeyPress-Return>', self.enterCallback)
		return self.entry

	def enterCallback(self, event):
		'''
		if this is a method, execute it when enter is pressed
		'''
		if isinstance(self.parent, Method):
			self.parent.butcom()

	def setWidget(self, value):
		if value is None:
			valuestr = ''
		else:
			valuestr = str(value)
		self.entry.delete(0,END)
		self.entry.insert(0,valuestr)

	def getWidget(self):
		valuestr = self.entry.get()
		if self.type == 'string':
			value = valuestr
		else:
			value = eval(valuestr)
		return value


class CheckbuttonData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)

	def buildWidget(self, parent):
		self.tkvar = BooleanVar()
		if self.styled:
			c = Checkbutton(parent, variable=self.tkvar, bg=self.buttoncolor)
		else:
			c = Checkbutton(parent, variable=self.tkvar)
		return c

	def setWidget(self, value):
		self.tkvar.set(value)

	def getWidget(self):
		value = self.tkvar.get()
		return value

class ComboboxData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)
		if self.choices is None:
			raise RuntimeError('need choices for ComboboxData')
		if self.choicestype != 'array':
			raise RuntimeError('ComboboxData requires array type choices')

	def buildWidget(self, parent):
		self.tkvar = StringVar()
		self.combo = Pmw.ComboBox(parent, entry_textvariable=self.tkvar)
		if self.styled:
			self.combo.component('entryfield').component('entry')['bg'] \
																														= self.entrycolor
		self.updateList()
		return self.combo

	def refresh(self, spec):
		Data.refresh(self, spec)
		self.updateList()

	def updateList(self):
		newlist = self.uiclient.execute('GET', (self.choicesid,))
		self.combo.setlist(newlist)

	def setWidget(self, value):
		if value is None:
			valuestr = ''
		else:
			valuestr = str(value)
		self.tkvar.set(valuestr)

	def getWidget(self):
		valuestr = self.tkvar.get()
		if self.type == 'string':
			value = valuestr
		else:
			value = eval(valuestr)
		return value

class DependentComboboxData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)
		if self.choices is None:
			raise RuntimeError('need choices for ComboboxData')
		if self.choicestype != 'struct':
			raise RuntimeError('DependentComboboxData requires struct type choices')

	def buildWidget(self, parent):
		self.tkvars = [StringVar(), StringVar()]
		self.comboframe = Frame(parent)
		choicedict = self.getChoiceDict()
		for i in self.levels:
			combo = Pmw.ComboBox(self.comboframe, entry_textvariable=self.tkvars[i])
			if self.styled:
				combo.component('entryfield').component('entry')['bg'] = self.entrycolor
			combo.pack(side=TOP)
			self.combos.append(combo)
			def callback():
				self.updateList(i+1)
			combo.component('entryfield')['modifiedcommand'] = junk

		self.updateLists()
		return self.comboframe

	def levels(self, tree):
		'''return the depth of a tree dict'''
		### this is not right
		if type(tree) in (tuple, list):
			return 1
		elif type(tree) is dict:
			try:
				child = tree.values()[0]
			except IndexError:
				pass

	def refresh(self, spec):
		Data.refresh(self, spec)
		self.updateChoiceDict()

	def getChoiceDict(self):
		choicedict = self.uiclient.execute('GET', (self.choicesid,))
		return choicedict

	def updateList(self, index, newlist):
		self.combos[index].setlist(newlist)

	def updateLists(self):
		for combo in self.combos:
			newlist = self.uiclient.execute('GET', (self.choices,))
			combo.setlist(newlist)

	def setWidget(self, values):
		if len(value) != self.levels:
			raise RuntimeError('require one value per combobox')
		i = 0
		for value in values:
			valuestr = str(value)
			self.tkvars[i].set(valuestr)
			i += 1

	def getWidget(self):
		values = []
		for tkvar in self.tkvars:
			valuestr = tkvar.get()
			if self.type == 'string':
				value = valuestr
			else:
				value = eval(valuestr)
			values.append(value)
		return values

class TreeSelectorData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)
		if self.type != 'array':
			raise RuntimeError('TreeSelectorData requires array type')

	def buildWidget(self, parent):
		mainframe = Frame(parent)
		if self.styled:
			self.sc = TreeWidget.ScrolledCanvas(mainframe, highlightthickness=0, bg=self.entrycolor)
		else:
			self.sc = TreeWidget.ScrolledCanvas(mainframe, highlightthickness=0)
		self.sc.frame.pack(expand=YES, fill=BOTH)
		choicedict = self.uiclient.execute('GET', (self.choicesid,))
		self.buildTree(choicedict)
		self.current = Frame(mainframe)
		self.current.pack()
		return mainframe

	def refresh(self, spec):
		Data.refresh(self, spec)
		choicedict = self.uiclient.execute('GET', (self.choicesid,))
		self.buildTree(choicedict)

	def buildTree(self, newdict):
		self.dict = newdict
		item = StructTreeItem(None, ' ', self.dict)
		node = JimsTreeNode(self.sc.canvas, None, item)
		node.expand()
		self.sc.canvas.selectedtrace = [' ',]

	def setWidget(self, value):
		#raise NotImplementedError()
		pass

	def getWidget(self):
		## return the path to the selected item
		return self.sc.canvas.selectedtrace[1:]


class TreeData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
#		self.dict = {}
		Data.__init__(self, parent, uiclient, spec, styled, server)
		if self.type != 'struct':
			raise RuntimeError('TreeData requires struct type')

	def buildWidget(self, parent):
#		self.treenode = None
#		if self.styled:
#			self.sc = TreeWidget.ScrolledCanvas(self, highlightthickness=0, bg=self.entrycolor, height=180, width=200)
#		else:
#			self.sc = TreeWidget.ScrolledCanvas(self, highlightthickness=0, bg='white', height=180, width=200)
#		return self.sc.frame
		self.tree = newtree.EntryTree(parent, {}, self.name, height=180, width=200)
		return self.tree

	def setWidget(self, value):
#		import copy
#		if self.dict == value:
#			return
#		if self.treenode is not None:
#			self.treenode.destroy()
#		if value is None:
#			self.dict = {}
#		else:
#			self.dict = copy.deepcopy(value)
#		item = StructTreeItem(None, self.name, self.dict)
#		self.treenode = TreeWidget.TreeNode(self.sc.canvas, None, item)
#		self.treenode.expand()
		self.tree.set(value)

	def getWidget(self):
#		return self.dict
		return self.tree.get()


class ImageData(Data):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		Data.__init__(self, parent, uiclient, spec, styled, server)
		if self.type != 'binary':
			raise RuntimeError('ImageData requires binary type')

	def buildWidget(self, parent):
		self.iv = ImageViewer(parent)
		self.iv.canvas.targetClickerOn()
		return self.iv

	def setWidget(self, value):
#		print 'setWidget'
		# value must be binary data from xmlrpc
		if not isinstance(value, xmlbinlib.Binary):
			print 'Error setting image: value must be instance of Binary'
			mrcstr = ''
		else:
			mrcstr = value.data

		#print 'length', len(mrcstr)
		#f = open('junkdata', 'w')
		#value.encode(f)
		#f.close()

		if mrcstr == '':
			self.iv.displayMessage('NO IMAGE DATA')
		else:
			t = Timer('converting mrcstr to numeric')
			numdata = Mrc.mrcstr_to_numeric(mrcstr)
			t.stop()
#			print 'DISPLAYING', numdata.typecode()
#			print 'import numeric'
			self.iv.import_numeric(numdata)
#			print 'done'


	def getWidget(self):
		'''
		this is how we return targets to the rpc server
		'''
		targets = self.getTargets()
		return targets

	def getTargets(self):
		'''
		call ImageCanvas.getTargets()
		then fix it up for xml-rpc
		'''
		targetlist = self.iv.canvas.getTargets()
		## remove items that are None
		for target in targetlist:
			for key, value in target.items():
				if value is None:
					del target[key]
		return targetlist


class Method(SpecWidget):
	def __init__(self, parent, uiclient, spec, styled=True, server=False):
		if styled:
			SpecWidget.__init__(self, parent, uiclient, spec, styled, server,
																										bd=3, relief=SOLID)
		else:
			SpecWidget.__init__(self, parent, uiclient, spec, styled, server)
		self.build()

	def build(self):
		self.name = self.spec['name']
		self.argspec = self.spec['argspec']
		
		if 'returnspec' in self.spec:
			self.returnspec = self.spec['returnspec']
		else:
			self.returnspec = None

		self.argwidgetsdict = {}
		self.argwidgetslist = []
		for arg in self.argspec:
			id = arg['id']
			dataclass = whichDataClass(arg)
			newwidget = dataclass(self, self.uiclient, arg, self.styled)
			newwidget.pack(expand=YES, fill=X)
			self.argwidgetsdict[id] = newwidget
			self.argwidgetslist.append(newwidget)

		if self.styled:
			but = Button(self, text=self.name, command=self.butcom,
																						bg=self.buttoncolor)
			but.pack()
		else:
			but = Button(self, text=self.name, command=self.butcom)
			but.pack(expand=YES, fill=X)

		if self.returnspec is not None:
			dataclass = whichDataClass(self.returnspec)
			self.retwidget = dataclass(self, self.uiclient, self.returnspec, self.styled)
			if self.retwidget is not None:
				self.retwidget.pack()
		else:
			self.retwidget = None

	def refresh(self, spec):
		SpecWidget.refresh(self, spec)
		for aspec in spec['argspec']:
			id = aspec['id']
			self.argwidgetsdict[id].refresh(aspec)

	def butcom(self):
		args = []
		for argwidget in self.argwidgetslist:
			newvalue = argwidget.getWidget()
			args.append(newvalue)
		args = tuple(args)
#		print 'executing %s' % (self.id,)
		ret = self.uiclient.execute(self.id, args)
		if ret is not None:
			t = Timer('process return')
			self.process_return(ret)
			t.stop()

	def process_return(self, returnvalue):
		if self.retwidget is not None:
			self.retwidget.setWidget(returnvalue)

class Server(xmlrpcserver.xmlrpcserver):
	def __init__(self, id, nodegui, port=None):
		self.nodegui = nodegui
		xmlrpcserver.xmlrpcserver.__init__(self, id, port=port)
		self.server.register_function(self.set, 'SET')

	def set(self, id, value):
		try:
			instance = self.nodegui.getWidgetInstance(id)
			if instance is not None:
				instance.setWidget(value)
			else:
				self.printerror('cannot find instance of %s to set' % str(id))
		except:
			return 0
		return ''

class NodeGUI(Frame):
	def __init__(self, parent, hostname=None, port=None, node=None, styled=True,
																																	server=False):
		#self.parent = parent
		self.styled = styled
		if (hostname is not None) and (port is not None):
			pass
		elif node is not None:
			hostname = node.location()['hostname']
			port = node.location()['UI port']
		else:
			raise RuntimeError('NodeGUI needs either node instance or hostname and port')

		Frame.__init__(self, parent)

		if server:
			self.server = Server(('UI client server',), self)
		else:
			self.server = None

		self.uiclient = interface.Client(hostname, port, self.server)

		self.__build()

	def getWidgetInstance(self, id):
		return self.mainframe.getWidgetInstance(id)

	def __build(self):
		if self.styled:
			f = Frame(self, bd=4, relief=SOLID)
		else:
			f = Frame(self)
		b=Button(f, text='Refresh', command=self.__refresh_components)
		b.pack(side=LEFT)

#		ngl = NodeGUILauncher(f)
#		ngl.pack(side=LEFT)

		f.pack(side=TOP, fill=BOTH)
		self.mainframe = None
		self.__build_components()

	def __refresh_components(self):
		spec = self.getSpec()
		self.mainframe.refresh(spec)

	def __build_components(self):
		if self.mainframe is not None:
			self.mainframe.destroy()
		spec = self.getSpec()
		if self.server is None:
			self.mainframe = NotebookContainer(self, self.uiclient, spec, self.styled)
		else:
			self.mainframe = NotebookContainer(self, self.uiclient, spec,
																												self.styled, True)
		self.name = self.mainframe.name
		self.mainframe.pack(expand=YES, fill=BOTH)

	def getSpec(self):
		spec = self.uiclient.getSpec()
		return spec

	def launchgui(self):
		host = self.launchhostent.get()
		port = self.launchportent.get()
		tk = self.newGUIWindow(host, port)

	def newGUIWindow(self, host, port):
		top = Toplevel()
		top.title('Node GUI')
		gui = NodeGUI(top, host, port)
		gui.pack(expand=YES, fill=BOTH)

# This was done quickly, should be thought out more I suppose
class StructTreeItem(TreeWidget.TreeItem):
	def __init__(self, parent, key, value):
		self.parent = parent
		self.key = key
		self.value = value

	def GetText(self):
		if self.key:
			return str(self.key)
		else:
			return str(self.value)

	def IsEditable(self):
		if self.key:
			return False
		else:
			return True

	def SetText(self, text):
		self.update(type(self.value)(text))

	def update(self, value):
		# bit hackish
		if type(self.value) is dict:
			self.value.update(value)
		else:
			self.value = value
		if self.parent:
			if type(self.parent.value) is dict:
				self.parent.update({self.key: self.value})
			else:
				self.parent.update(self.value)

	def GetIconName(self):
		if not self.IsExpandable():
			return "python"

	def IsExpandable(self):
		if self.key:
			return True
		else:
			return False

	def GetSubList(self):
		if type(self.value) is dict:
			sublist = []
			value = self.value.keys()
			value.sort()
			for k in value: 
				item = StructTreeItem(self, k, self.value[k])
				sublist.append(item)
			return sublist
		elif type(self.value) in (tuple,list):
			sublist = []
			if type(self.value) == list:
				self.value.sort()
			for k in self.value:
				item = StructTreeItem(self, None, k)
				sublist.append(item)
			return sublist
		else:
			return [StructTreeItem(self, None, self.value)]

	def traceBack(self):
		if self.key:
			name = self.key
		else:
			name = self.value

		if self.parent is None:
			return  (name,)
		else:
			parents = self.parent.traceBack()
			return parents + (name,)

class JimsTreeNode(TreeWidget.TreeNode):
	def __init__(self, canvas, parent, item):
		TreeWidget.TreeNode.__init__(self, canvas, parent, item)

	def select(self, event=None):
		TreeWidget.TreeNode.select(self, event)
		self.canvas.selectedtrace = self.traceBack()

	def traceBack(self):
		trace = self.item.traceBack()
		return trace

	## copied from TreeWidget.TreeNode
	## changed TreeNode to JimsTreeNode
	def draw(self, x, y):

		# XXX This hard-codes too many geometry constants!
		self.x, self.y = x, y
		self.drawicon()
		self.drawtext()
		if self.state != 'expanded':
			return y+17
		# draw children
		if not self.children:
		    sublist = self.item._GetSubList()
		    if not sublist:
			# _IsExpandable() was mistaken; that's allowed
			return y+17
		    for item in sublist:
			child = JimsTreeNode(self.canvas, self, item)
			self.children.append(child)
		cx = x+20
		cy = y+17
		cylast = 0
		for child in self.children:
		    cylast = cy
		    self.canvas.create_line(x+9, cy+7, cx, cy+7, fill="gray50")
		    cy = child.draw(cx, cy)
		    if child.item._IsExpandable():
			if child.state == 'expanded':
			    iconname = "minusnode"
			    callback = child.collapse
			else:
			    iconname = "plusnode"
			    callback = child.expand
			image = self.geticonimage(iconname)
			id = self.canvas.create_image(x+9, cylast+7, image=image)
			# XXX This leaks bindings until canvas is deleted:
			self.canvas.tag_bind(id, "<1>", callback)
			self.canvas.tag_bind(id, "<Double-1>", lambda x: None)
		id = self.canvas.create_line(x+9, y+10, x+9, cylast+7,
		    ##stipple="gray50",     # XXX Seems broken in Tk 8.0.x
		    fill="gray50")
		self.canvas.tag_lower(id) # XXX .lower(id) before Python 1.5.2
		return cy


#class ComboBoxDropdownCallback(Pmw.ComboBox):
#	def __init__(self, parent = None, callback = None, **kw):
#		self.callback = callback
#		INITOPT = Pmw.INITOPT
#		optiondefs = (
#		    ('autoclear',          0,          INITOPT),
#		    ('buttonaspect',       1.0,        INITOPT),
#		    ('dropdown',           1,          INITOPT),
#		    ('fliparrow',          0,          INITOPT),
#		    ('history',            1,          INITOPT),
#		    ('labelmargin',        0,          INITOPT),
#		    ('labelpos',           None,       INITOPT),
#		    ('listheight',         150,        INITOPT),
#		    ('selectioncommand',   '',         None),
#		    ('unique',             1,          INITOPT),
#		)
#		self.defineoptions(kw, optiondefs)
#		Pmw.ComboBox.__init__(self, parent)
#		self.initialiseoptions()
#
#	def _postList(self, event = None):
#		if callable(self.callback):
#			self.callback()
#		Pmw.ComboBox._postList(self, event)

class NodeGUILauncher(Frame):
	def __init__(self, parent, hostname=None, port=None):
		#self.parent = parent
		if hostname is not None and port is not None:
			self.uiclient = interface.Client(hostname, port)
			self.getNodeLocations()
		Frame.__init__(self, parent)
		self.__build()

	def __build(self):
		self.notebook = Pmw.NoteBook(self)
		connectframe = self.notebook.add('Connect')
		automaticframe = self.notebook.add('Automatic')
		manualframe = self.notebook.add('Manual')

		##################################################
		
		launchframe = Frame(manualframe, bd=4, relief=SOLID)
		launchhostport = HostPortSelector(launchframe, buttontext='Launch GUI', callback=self.launchgui)
		launchhostport.pack()
		launchframe.pack()

		###############################################

		managerframe = Frame(connectframe, bd=4, relief=SOLID)

		mllabel = Label(managerframe, text='Manager UI Server:')
		mlhostport = HostPortSelector(managerframe, buttontext='Connect', callback = self.setManagerLocation)
		statusframe = Frame(managerframe)
		mlstatuslab = Label(statusframe, text='Status:  ')
		self.mlstatus = Label(statusframe, text='Not Connected')

		mllabel.pack(side=TOP)
		mlhostport.pack(side=TOP)
		mlstatuslab.pack(side=LEFT)
		self.mlstatus.pack(side=LEFT)
		statusframe.pack(side=TOP)

		managerframe.pack(side=TOP, fill=BOTH)

		nodeidframe = Frame(automaticframe, bd=4, relief=SOLID)

		nglabel = Label(nodeidframe, text='Node UI:')
		nodeidlabel = Label(nodeidframe, text='Node ID')
		self.nodeidsvar = StringVar()
		self.nodeidsentry = Pmw.ComboBox(nodeidframe, entry_textvariable=self.nodeidsvar)
		self.nodeidsentry.component('entryfield').component('entry')['width'] = 20
		self.launchuibutton = Button(nodeidframe, text='Launch', command=self.launchUIbyNodeID, state=DISABLED)
		self.refreshbutton = Button(nodeidframe, text='Refresh', command=self.getNodeLocations, state=DISABLED)

		nglabel.pack(side=TOP)
		nodeidlabel.pack(side=LEFT)
		self.nodeidsentry.pack(side=LEFT)
		self.launchuibutton.pack(side=LEFT)
		self.refreshbutton.pack(side=LEFT)

		nodeidframe.pack(side=TOP, fill=BOTH)

		self.notebook.pack(fill=BOTH, expand=YES)
		self.notebook.setnaturalsize()

	def setManagerLocation(self, hostname, uiport):
		self.uiclient = interface.Client(hostname, uiport)
		try:
			self.getNodeLocations()
			self.mlstatus['text'] = 'Connected'
			self.launchuibutton['state'] = NORMAL
			self.refreshbutton['state'] = NORMAL
		except socket.error:
			self.mlstatus['text'] = 'Failed to connect to UI Server'
			print 'Failed to connect to UI Server'

	def getNodeLocations(self):
		self.nodelocations = self.uiclient.execute("getNodeLocations")
		self.nodeidsentry.setlist(self.nodelocations.keys())

		try:
			self.nodeidsentry.selectitem(index=0, setentry=1)
		except IndexError:
			self.nodeidsentry.clear()

	def launchUIbyNodeID(self):
		nodeid = self.nodeidsvar.get()
		try:
			hostname = self.nodelocations[nodeid]['hostname']
			uiport = self.nodelocations[nodeid]['UI port']
			print "Launching interface to '%s' on %s:%d" % (nodeid, hostname, uiport)
			tk = self.newGUIWindow(hostname, uiport)
		except:
			print "Error: cannot launch '%s' by ID" % nodeid

	def launchgui(self, host, port):
		tk = self.newGUIWindow(host, port)

	def newGUIWindow(self, host, port):
		top = Toplevel()
		top.title('Node GUI')
		try:
			gui = NodeGUI(top, host, port)
			gui.pack(expand=YES, fill=BOTH)
			return top
		except Exception, detail:
			print 'UI DETAIL', detail
			top.destroy()
			print "Error: cannot create new UI window for %s:%s" % (host, port)
			return None

class NodeUILauncher(Frame):
	def __init__(self, parent, hostname, port):
		#self.parent = parent
		Frame.__init__(self, parent)
		self.__build()
		self.uiclient = interface.Client(hostname, port)
		self.getNodeLocations()
		for l in self.nodelocations:
			hostname = self.nodelocations[l]['hostname']
			uiport = self.nodelocations[l]['UI port']
			self.newGUIWindow(hostname, uiport)
			

	def __build(self):
		nodeidframe = Frame(self, bd=4, relief=SOLID)

		nglabel = Label(nodeidframe, text='Node UI:')
		nodeidlabel = Label(nodeidframe, text='Node ID')
		self.nodeidsvar = StringVar()
		self.nodeidsentry = Pmw.ComboBox(nodeidframe, entry_textvariable=self.nodeidsvar)
		self.nodeidsentry.component('entryfield').component('entry')['width'] = 20
		launchuibutton = Button(nodeidframe, text='Launch', command=self.launchUIbyNodeID)
		refreshbutton = Button(nodeidframe, text='Refresh', command=self.getNodeLocations)

		nglabel.pack(side=TOP)
		nodeidlabel.pack(side=LEFT)
		self.nodeidsentry.pack(side=LEFT)
		launchuibutton.pack(side=LEFT)
		refreshbutton.pack(side=LEFT)

		nodeidframe.pack(side=TOP, fill=BOTH)

	def getNodeLocations(self):
		try:
			self.nodelocations = self.uiclient.execute("getNodeLocations")
		except:
			self.nodelocations = {}

		self.nodeidsentry.setlist(self.nodelocations.keys())

		try:
			self.nodeidsentry.selectitem(index=0, setentry=1)
		except IndexError:
			self.nodeidsentry.clear()

	def launchUIbyNodeID(self):
		nodeid = self.nodeidsvar.get()
		try:
			hostname = self.nodelocations[nodeid]['hostname']
			uiport = self.nodelocations[nodeid]['UI port']
			print "Launching interface to '%s' on %s:%d" % (nodeid, hostname, uiport)
			self.newGUIWindow(hostname, uiport)
		except:
			print "Error: cannot launch '%s' by ID" % nodeid

	def newGUIWindow(self, host, port):
		top = Toplevel()
		top.title('Node GUI')
		try:
			gui = NodeGUI(top, host, port)
			gui.pack(expand=YES, fill=BOTH)
			return top
		except:
			top.destroy()
			print "Error: cannot create new UI window for %s:%s" % (host, port)
			return None

class HostPortSelector(Frame):
	'''
	HostPortSelector(parent, buttontext, callback)
	This is a hostname/port selector widget
	callback must take two arguments:  hostname, and port
	'''
	def __init__(self, parent, buttontext, callback):
		Frame.__init__(self, parent)

		defaulthost = socket.gethostname()
		self.externalCallback = callback
		self.hosthistory = [defaulthost,]


		hostnamelabel = Label(self, text='Host')

		self.hostnamevar = StringVar()
		self.hostnameentry = Pmw.ComboBox(self, entry_textvariable=self.hostnamevar)
		self.hostnameentry.setlist(self.hosthistory)
		self.hostnameentry.component('entryfield').component('entry')['width'] = 12
		self.hostnamevar.set(defaulthost)
		self.hostnameentry.bind('<KeyPress-Return>', self.localCallback)

		portlabel = Label(self, text='Port')

		self.portentry = Pmw.Counter(self, datatype='integer')
		self.portentry.component('entryfield').component('entry')['width'] = 5
		portentry = self.portentry.component('entry')
		portentry.insert(0, 49153)
		portentry.bind('<KeyPress-Return>', self.localCallback)

		button = Button(self, text=buttontext, command=self.localCallback)

		hostnamelabel.pack(side=LEFT)
		self.hostnameentry.pack(side=LEFT)
		portlabel.pack(side=LEFT)
		self.portentry.pack(side=LEFT)
		button.pack(side=LEFT)

	def localCallback(self):
		host = self.hostnamevar.get()
		port = self.portentry.get()
		self.externalCallback(host, port)
		self.addHostHistory(host)

	def addHostHistory(self, host):
		if host not in self.hosthistory:
			self.hosthistory.append(host)
			self.hostnameentry.setlist(self.hosthistory)


if __name__ == '__main__':
	import sys

	root = Tk()
	root.wm_title('Node GUI Launcher')

	if len(sys.argv) == 3:
		hostname = sys.argv[1]
		port = int(sys.argv[2])
		gui = NodeGUI(root, hostname, port)
	else:
		gui = NodeGUILauncher(root)

	gui.pack(expand=YES, fill=BOTH)
	root.mainloop()

