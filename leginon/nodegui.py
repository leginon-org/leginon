#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface
# why doesn't this work? add <python dir>\Tools\idle to your PYTHONPATH
import TreeWidget
import os
import threading
import socket

False=0
True=1

class SpecWidget(Frame):
	def __init__(self, parent, uiclient, spec, **kwargs):
		Frame.__init__(self, parent, **kwargs)
		self.spec = spec
		self.id = self.spec['id']
		self.uiclient = uiclient
		self['bg'] = '#4488BB'
		self.buttoncolor = '#7AA6C5'
		self.entrycolor = '#FFF'

	def refresh(self, spec):
		self.spec = spec

class Container(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec)
		self.label = Label(self, text=spec['name'], bg=self['bg'])
		self.label.pack()
		self.name = spec['name']
		self.build()

	def build(self):
		content = self.spec['content']
		self.content = {}
		for spec in content:
			id = spec['id']
			w = widgetFromSpec(self, self.uiclient, spec)
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

class NotebookContainer(Container):
	def __init__(self, parent, uiclient, spec):
		Container.__init__(self, parent, uiclient, spec)

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

			w = widgetFromSpec(newframe, self.uiclient, spec)
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

def widgetFromSpec(parent, uiclient, spec):
	spectype = spec['spectype']
	if spectype == 'container':
		widget = Container(parent, uiclient, spec)
	elif spectype == 'method':
		widget = Method(parent, uiclient, spec)
	elif spectype == 'data':
		dataclass = whichDataClass(spec)
		widget = dataclass(parent, uiclient, spec)
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
	else:
		raise RuntimeError('type not supported')

class Data(SpecWidget):
	def __init__(self, parent, uiclient, spec):

		SpecWidget.__init__(self, parent, uiclient, spec, bd=2, relief=SOLID)
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

		if 'default' in spec:
			self.default = spec['default']
		else:
			self.default = None

	def build(self):
		headframe = Frame(self)

		### label
		lab = Label(headframe, text=self.name, bg=self['bg'])
		lab.pack(side=LEFT, fill=BOTH)

		### optional get/set
		if self.permissions is not None:
			if 'r' in self.permissions:
				Button(headframe, text='Get', command=self.getServer, bg=self.buttoncolor).pack(side=LEFT)
			if 'w' in self.permissions:
				Button(headframe, text='Set', command=self.setServer, bg=self.buttoncolor).pack(side=LEFT)

		headframe.pack(side=TOP)

		### the actual data widget
		w = self.buildWidget(self)
		if self.default is not None:
			self.setWidget(self.default)
		w.pack(side=TOP, expand=YES, fill=BOTH)

	def refresh(self, spec):
		SpecWidget.refresh(self, spec)
		self.initInfo(spec)
		if self.default is not None:
			self.setWidget(self.default)

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
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)

	def buildWidget(self, parent):
		self.entry = Entry(parent, width=10, bg=self.entrycolor)
		return self.entry

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
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)

	def buildWidget(self, parent):
		self.tkvar = BooleanVar()
		c = Checkbutton(parent, variable=self.tkvar, bg=self.buttoncolor)
		return c

	def setWidget(self, value):
		self.tkvar.set(value)

	def getWidget(self):
		value = self.tkvar.get()
		return value

class ComboboxData(Data):
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)
		if self.choices is None:
			raise RuntimeError('need choices for ComboboxData')
		if self.choicestype != 'array':
			raise RuntimeError('ComboboxData requires array type choices')

	def buildWidget(self, parent):
		self.tkvar = StringVar()
		self.combo = Pmw.ComboBox(parent, entry_textvariable=self.tkvar)
		self.combo.component('entryfield').component('entry')['bg'] = self.entrycolor
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
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)
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
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)
		if self.type != 'array':
			raise RuntimeError('TreeSelectorData requires array type')

	def buildWidget(self, parent):
		mainframe = Frame(parent)
		self.sc = TreeWidget.ScrolledCanvas(mainframe, highlightthickness=0, bg=self.entrycolor)
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
		raise NotImplementedError()

	def getWidget(self):
		## return the path to the selected item
		return self.sc.canvas.selectedtrace[1:]


class TreeData(Data):
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)
		if self.type != 'struct':
			raise RuntimeError('TreeData requires struct type')

	def buildWidget(self, parent):
		self.sc = None
		self.treeframe = Frame(parent)
		return self.treeframe

	def setWidget(self, value):
		self.dict = value
		if self.sc is not None:
			self.sc.frame.destroy()
		self.sc = TreeWidget.ScrolledCanvas(self.treeframe, highlightthickness=0, bg=self.entrycolor)
		item = StructTreeItem(None, self.name, self.dict)
		node = TreeWidget.TreeNode(self.sc.canvas, None, item)
		node.expand()
		self.sc.frame.pack(expand=YES, fill=BOTH)

	def getWidget(self):
		return self.dict


class Method(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec, bd=3, relief=SOLID)
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
			newwidget = dataclass(self, self.uiclient, arg)
			newwidget.pack(expand=YES, fill=X)
			self.argwidgetsdict[id] = newwidget
			self.argwidgetslist.append(newwidget)

		but = Button(self, text=self.name, command=self.butcom, bg=self.buttoncolor)
		but.pack()

		if self.returnspec is not None:
			dataclass = whichDataClass(self.returnspec)
			self.retwidget = dataclass(self, self.uiclient, self.returnspec)
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
		ret = self.uiclient.execute(self.id, args)
		self.process_return(ret)

	def process_return(self, returnvalue):
		if self.retwidget is not None:
			self.retwidget.setWidget(returnvalue)

	def init_return(self, returntype):
		'''
		set up for handling return values
		return a widget if one was created
		'''
		self.returntype = returntype
		if returntype in ('array','string'):
			wid = Frame(self)
			widlab = Label(wid, text='Result:',bg=self['bg'])
			self.retwidget = Text(wid, height=1,width=30,wrap=NONE)
			self.retwidget['state'] = DISABLED
			retscroll = Scrollbar(wid, orient=HORIZONTAL)
			retscroll['command'] = self.retwidget.xview
			self.retwidget['xscrollcommand'] = retscroll.set
			widlab.grid(row=0,column=0,rowspan=2)
			self.retwidget.grid(row=0, column=1)
			retscroll.grid(row=1,column=1,sticky=EW)
			return wid
		if returntype == 'struct':
			self.retwidget = TreeWidget.ScrolledCanvas(self, bg='white', highlightthickness=0)
			return self.retwidget.frame
		else:
			return None


class NodeGUI(Frame):
	def __init__(self, parent, hostname=None, port=None, node=None):
		#self.parent = parent
		if (hostname is not None) and (port is not None):
			pass
		elif node is not None:
			hostname = node.location()['hostname']
			port = node.location()['UI port']
		else:
			raise RuntimeError('NodeGUI needs either node instance or hostname and port')

		Frame.__init__(self, parent)
		self.uiclient = interface.Client(hostname, port)
		self.__build()

	def __build(self):
		f = Frame(self, bd=4, relief=SOLID)
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
		self.mainframe = NotebookContainer(self, self.uiclient, spec)
		self.name = self.mainframe.name
		self.mainframe.pack(expand=YES, fill=BOTH)

	def getSpec(self):
		return self.uiclient.getSpec()

	def launchgui(self):
		host = self.launchhostent.get()
		port = self.launchportent.get()
		tk = self.newGUIWindow(host, port)

	def newGUIWindow(self, host, port):
		top = Toplevel()
		top.title('Node GUI')
		gui = NodeGUI(top, host, port)
		gui.pack(expand=YES, fill=BOTH)

#	t = threading.Thread(target=tk.mainloop)
#	t.setDaemon(1)
#	t.start()
#	tk.mainloop()
#	return tk

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
			for k in self.value:
				item = StructTreeItem(self, k, self.value[k])
				sublist.append(item)
			return sublist
		elif type(self.value) in (tuple,list):
			sublist = []
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


class NodeGUILauncher(Frame):
	def __init__(self, parent):
		#self.parent = parent
		Frame.__init__(self, parent)
		self.__build()

	def __build(self):
		f = Frame(self, bd=4, relief=SOLID)

		launchbut = Button(f, text='Launch GUI', command=self.launchgui)
		launchhostlab = Label(f, text='Host')
		self.launchhostent = Entry(f, width=15)
		defaulthost = socket.gethostname()
		self.launchhostent.insert(0, defaulthost)
		launchportlab = Label(f, text='Port')

		self.launchportent = Pmw.Counter(f, datatype='integer')
		portent = self.launchportent.component('entry')
		portent.insert(0, 49152)


		launchbut.pack(side=LEFT)
		launchhostlab.pack(side=LEFT)
		self.launchhostent.pack(side=LEFT)
		launchportlab.pack(side=LEFT)
		self.launchportent.pack(side=LEFT)

		self.launchhostent.bind('<KeyPress-Return>', self.launchgui)
		portent.bind('<KeyPress-Return>', self.launchgui)

		f.pack(side=TOP, fill=BOTH)

	def launchgui(self, event=None):
		host = self.launchhostent.get()
		port = self.launchportent.get()
		tk = self.newGUIWindow(host, port)

	def newGUIWindow(self, host, port):
		top = Toplevel()
		top.title('Node GUI')
		try:
			gui = NodeGUI(top, host, port)
			gui.pack(expand=YES, fill=BOTH)
		except:
			top.destroy()

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

