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
		self.buildSpec()

	def buildSpec(self):
		raise NotImplementedError()


### maybe should subclass Data to get specific types:  Combobox, Tree, ...
class Data(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		self.bgcolor = 'cyan'
		SpecWidget.__init__(self, parent, uiclient, spec, bd=1, relief=SUNKEN, bg=self.bgcolor)

	def buildSpec(self):
		name = self.name = self.spec['name']
		self.type = self.spec['xmlrpctype']
		self.enum = self.spec['enum']
		self.permissions = self.spec['permissions']

		if 'default' in self.spec:
			self.default = self.spec['default']
		else:
			self.default = None

		if len(self.enum) > 0:
			self.arg_choice(name, self.enum)
		elif self.type == 'boolean':
			self.arg_check(name)
		elif self.type in ('integer', 'float', 'string'):
			self.arg_entry(name, self.type)
		elif self.type == 'array':
			self.arg_entry(name, self.type)
		elif self.type == 'struct':
			self.arg_entry(name, self.type)
		elif self.type == 'date':
			self.arg_date(name)
		elif self.type == 'binary':
			self.arg_binary(name)
		else:
			raise RuntimeError('type not supported')

		## sets the initial value
		if self.default is not None:
			self.tkvar.set(self.default)

	def set(self, value):
		if self.type == 'struct':
			self.struct = value
		else:
			self.tkvar.set(value)

	def get(self):
		if type(self.type) is dict:
			return self.struct
		else:
			return self.tkvar.get()

	def setServer(self):
		value = self.get()
		r = self.uiclient.execute('SET', (self.name, value))
		self.set(r)

	def getServer(self):
		r = self.uiclient.execute('GET', (self.name,))
		self.set(r)

# types:
#('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')
	def arg_choice(self, name, choices):
		self.tkvar = StringVar()
		Label(self, text=name, bg=self.bgcolor).pack(side=LEFT)
		cb = Pmw.ComboBox(self, entry_textvariable=self.tkvar)
		##cb['bg'] = self.bgcolor
		cb.setlist(choices)
		cb.pack(side=LEFT)
		self.datawidget = cb

	def arg_check(self, name):
		self.tkvar = BooleanVar()
		self.datawidget = Checkbutton(self, text=name, variable=self.tkvar, bg=self.bgcolor)
		self.datawidget.pack(side=LEFT)

	def arg_entry(self, name, type):
			

		if type == 'integer':
			self.tkvar = IntVar()
		if type == 'float':
			self.tkvar = DoubleVar()
		if type == 'string':
			self.tkvar = StringVar()
		if type == 'array':
			self.tkvar = StringVar()
		if type == 'struct':
			self.tkvar = StringVar()
		Label(self, text=name, bg=self.bgcolor).pack(side=LEFT)
		if self.permissions == 'rw':
			Button(self, text='Set', command=self.setServer).pack()
			Button(self, text='Get', command=self.getServer).pack()
		self.datawidget = Entry(self, textvariable=self.tkvar, width=10, bg=self.bgcolor)
		self.datawidget.pack(side=LEFT)

	def arg_array(self, name):
		raise NotImplementedError

	def arg_struct(self, name, struct):
		self.struct = struct
		sc = TreeWidget.ScrolledCanvas(self, highlightthickness=0, bg=self.bgcolor)
		sc.frame.pack()
		item = StructTreeItem(None, name, self.struct)
		node = TreeWidget.TreeNode(sc.canvas, None, item)
		node.expand()
		self.datawidget = sc
		
	def arg_date(self, name):
		raise NotImplementedError

	def arg_binary(self, name):
		raise NotImplementedError


class Container(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec)

	def buildSpec(self):
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
				widget = Data(self, self.uiclient, spec)
			else:
				raise RuntimeError('invalid spec type')
			widget.pack()

class Method(SpecWidget):
	def __init__(self, parent, uiclient, spec):
		SpecWidget.__init__(self, parent, uiclient, spec, bd=3, relief=SOLID, bg='yellow')

	def buildSpec(self):
		self.name = self.spec['name']
		self.argspec = self.spec['argspec']
		
		if 'returnspec' in self.spec:
			self.returnspec = self.spec['returnspec']
		else:
			self.returnspec = None

		self.argwidgets = []
		for arg in self.argspec:
			newwidget = Data(self, self.uiclient, arg)
			newwidget.pack()
			self.argwidgets.append(newwidget)

		but = Button(self, text=self.name, command=self.butcom)
		but.pack()

		if self.returnspec is not None:
			retwidget = Data(self, self.uiclient, self.returnspec)
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
		ret = self.returnspec['xmlrpctype']
		if ret in ('array','string'):
			print 'retwidget', self.retwidget
			self.retwidget['state'] = NORMAL
			self.retwidget.delete(0,END)
			self.retwidget.insert(0, `returnvalue`)
			self.retwidget['state'] = DISABLED
		if ret == 'struct':
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

		mainframe = Container(self, self.uiclient, self.uiclient.spec)
		mainframe.pack()

		#self.id = self.uiclient.execute('ID')
		#print 'ID', self.id
		#self.components = {}
		#self.__build()

	def __build(self):
		f = Frame(self, bd=4, relief=SOLID)
		l = Label(f, text=`self.id`)
		l.pack(side=TOP)
		b=Button(f, text='Refresh', command=self.__build_components)
		b.pack(side=TOP)
		f.pack(side=TOP, expand=YES, fill=BOTH)
		self.__build_components()

	def __build_components(self):
		## destroy components if this is a refresh
		for value in self.components.values():
			value.destroy()
		self.components.clear()

		self.uiclient.getMethods()
			
		for key in self.uiclient.funclist:
			value = self.uiclient.funcdict[key]
			c = NodeGUIComponent(self, value)
			c.pack(side=TOP, expand=YES, fill=BOTH)
			self.components[key] = c
		
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
