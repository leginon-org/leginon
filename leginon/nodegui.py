#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface
# why doesn't this work? add <python dir>\Tools\idle to your PYTHONPATH
import TreeWidget
import os

class SpecWidget(Frame):
	def __init__(self, parent, uiclient, spec, **kwargs):
		Frame.__init__(self, parent, **kwargs)
		self.spec = spec
		self.uiclient = uiclient

class Container(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec, bg='cyan')
		self.build()

	def build(self):
		self.name = self.spec['name']
		self.label = Label(self, text = self.name)
		self.label.pack()
		for spec in self.spec['content']:
			spectype = spec['spectype']
			if spectype == 'container':
				widget = Container(self, self.uiclient, spec)
			elif spectype == 'method':
				widget = Method(self, self.uiclient, spec)
			elif spectype == 'data':
				dataclass = whichDataClass(spec)
				widget = dataclass(self, self.uiclient, spec)
			else:
				raise RuntimeError('invalid spec type')
			widget.pack(side=TOP)

class NotebookContainer(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec, bg='cyan')
		self.build()

	def build(self):
		self.name = self.spec['name']
		self.label = Label(self, text = self.name)
		self.label.pack()

		self.notebook = Pmw.NoteBook(self)
		for spec in self.spec['content']:
			name = spec['name']
			spectype = spec['spectype']
			newframe = self.notebook.add(name)
			if spectype == 'container':
				widget = Container(newframe, self.uiclient, spec)
			elif spectype == 'method':
				widget = Method(newframe, self.uiclient, spec)
			elif spectype == 'data':
				dataclass = whichDataClass(spec)
				widget = dataclass(newframe, self.uiclient, spec)
			else:
				raise RuntimeError('invalid spec type')
			widget.pack(side=TOP)

		self.notebook.pack(fill=BOTH, expand=YES)


def whichDataClass(dataspec):
	'''this checks a data spec to figure out what Data class to use'''
	type = dataspec['xmlrpctype']
	if 'enum' in dataspec:
		enum = dataspec['enum']
	else:
		enum = None

	if enum is not None:
		return ComboboxData

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
		self.bgcolor = None

		SpecWidget.__init__(self, parent, uiclient, spec, bd=2, relief=SUNKEN, bg=self.bgcolor)

		self.name = self.spec['name']
		self.type = self.spec['xmlrpctype']
		if 'enum' in self.spec:
			self.enum = self.spec['enum']
		else:
			self.enum = None
		if 'permissions' in self.spec:
			self.permissions = self.spec['permissions']
		else:
			self.permissions = None

		if 'default' in self.spec:
			self.default = self.spec['default']
		else:
			self.default = None

		headframe = Frame(self)

		### label
		lab = Label(headframe, text=self.name, bg=self.bgcolor)
		lab.pack(side=LEFT)

		### optional get/set
		if self.permissions is not None:
			if 'r' in self.permissions:
				Button(headframe, text='Get', command=self.getServer).pack(side=LEFT)
			if 'w' in self.permissions:
				Button(headframe, text='Set', command=self.setServer).pack(side=LEFT)

		headframe.pack(side=TOP)

		### the actual data widget
		w = self.buildWidget(self)
		w.pack(side=TOP)

	def setServer(self):
		value = self.getWidget()
		r = self.uiclient.execute('SET', (self.name, value))
		self.setWidget(r)

	def getServer(self):
		r = self.uiclient.execute('GET', (self.name,))
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
		self.entry = Entry(parent, width=10, bg=self.bgcolor)
		return self.entry

	def setWidget(self, value):
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
		c = Checkbutton(parent, variable=self.tkvar, bg=self.bgcolor)
		return c

	def setWidget(self, value):
		self.tkvar.set(value)

	def getWidget(self):
		value = self.tkvar.get()
		return value

class ComboboxData(Data):
	def __init__(self, parent, uiclient, spec):
		Data.__init__(self, parent, uiclient, spec)
		if 'enum' not in self.spec:
			raise RuntimeError('need enum for ComboboxData')

	def buildWidget(self, parent):
		self.tkvar = StringVar()
		self.combo = Pmw.ComboBox(parent, entry_textvariable=self.tkvar)
		self.updateList()
		return self.combo

	def updateList(self):
		newlist = self.uiclient.execute('GET', (self.enum,))
		self.combo.setlist(newlist)

	def setWidget(self, value):
		self.tkvar.set(value)

	def getWidget(self):
		valuestr = self.tkvar.get()
		if self.type == 'string':
			value = valuestr
		else:
			value = eval(valuestr)
		return value

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
		if self.sc is not None:
			self.sc.frame.destroy()

		self.sc = TreeWidget.ScrolledCanvas(self.treeframe, highlightthickness=0, bg=self.bgcolor)
		item = StructTreeItem(None, self.name, value)
		node = TreeWidget.TreeNode(self.sc.canvas, None, item)
		node.expand()
		self.sc.frame.pack()

	def getWidget(self):
		raise NotImplementedError()


class Method(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec, bd=3, relief=SOLID, bg='green')
		self.build()

	def build(self):
		self.name = self.spec['name']
		self.argspec = self.spec['argspec']
		
		if 'returnspec' in self.spec:
			self.returnspec = self.spec['returnspec']
		else:
			self.returnspec = None

		self.argwidgets = []
		for arg in self.argspec:
			dataclass = whichDataClass(arg)
			newwidget = dataclass(self, self.uiclient, arg)
			newwidget.pack()
			self.argwidgets.append(newwidget)

		but = Button(self, text=self.name, command=self.butcom)
		but.pack()

		if self.returnspec is not None:
			dataclass = whichDataClass(self.returnspec)
			retwidget = dataclass(self, self.uiclient, self.returnspec)
			self.retwidget = retwidget.datawidget
			if retwidget is not None:
				retwidget.pack()

	def butcom(self):
		newargs = []
		for argwidget in self.argwidgets:
			newvalue = argwidget.get()
			newargs.append(newvalue)
		ret = self.uiclient.execute(self.name, newargs)
		self.process_return(ret)

	def process_return(self, returnvalue):
		if self.returnspec is None:
			return
		ret = self.returnspec['xmlrpctype']
		if ret in ('array','string'):
			self.retwidget['state'] = NORMAL
			self.retwidget.delete(0,END)
			self.retwidget.insert(0, `returnvalue`)
			self.retwidget['state'] = DISABLED
		elif ret == 'struct':
			item = StructTreeItem(None, 'Result', returnvalue)
			node = TreeWidget.TreeNode(self.retwidget.canvas, None, item)
			node.expand()
#			self.retwidget['state'] = NORMAL
#			self.retwidget['height'] = len(returnvalue)
#			self.retwidget.delete(1.0,END)
#			for key,value in returnvalue.items():
#				rowstr = key + ': ' + `value` + '\n'
#				self.retwidget.insert(END, rowstr)
#			self.retwidget['state'] = DISABLED
		else:
			pass

	def init_return(self, returntype):
		'''
		set up for handling return values
		return a widget if one was created
		'''
		self.returntype = returntype
		if returntype in ('array','string'):
			wid = Frame(self)
			widlab = Label(wid, text='Result:')
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
		b=Button(f, text='Refresh', command=self.__build_components)
		b.pack(side=TOP)
		f.pack(side=TOP, expand=YES, fill=BOTH)
		self.mainframe = None
		self.__build_components()

	def __build_components(self):
		if self.mainframe is not None:
			self.mainframe.destroy()
		self.mainframe = NotebookContainer(self, self.uiclient, self.uiclient.spec)
		self.mainframe.pack()


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
		else:
			return [StructTreeItem(self, None, self.value)]

if __name__ == '__main__':
	import sys

	tk = Tk()
	hostname = sys.argv[1]
	port = sys.argv[2]
	gui = NodeGUI(tk, sys.argv[1], sys.argv[2])
	#newtitle = 'Interface to %s' % gui.id
	#tk.wm_title(newtitle)
	gui.pack()
	tk.mainloop()
