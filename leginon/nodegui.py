#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface
# why doesn't this work? add <python dir>\Tools\idle to your PYTHONPATH
import TreeWidget
import os

class NodeGUIArg(Frame):
	def __init__(self, parent, argname, argalias, argtype, argvalue=None):
		Frame.__init__(self, parent)
		self.name = argname
		self.type = argtype
		self.alias = argalias
		if argtype == 'boolean':
			self.arg_boolean(argalias)
		elif argtype == 'integer':
			self.arg_integer(argalias)
		elif argtype == 'float':
			self.arg_float(argalias)
		elif argtype == 'string':
			self.arg_string(argalias)
		elif argtype == 'array':
			self.arg_array(argalias)
		elif type(argtype) == dict:
			self.arg_struct(argalias, argtype)
		elif argtype == 'date':
			self.arg_date(argalias)
		elif argtype == 'binary':
			self.arg_binary(argalias)
		elif type(argtype) in (list,tuple):
			self.arg_choice(argalias, argtype)
		else:
			raise RuntimeError('argtype not supported')

		## sets the initial value
		if argvalue is not None:
			self.tkvar.set(argvalue)

	def get(self):
		return self.tkvar.get()

# types:
#('boolean', 'integer', 'float', 'string', 'array', 'struct', 'date', 'binary')
	def arg_choice(self, name, choices):
		self.tkvar = StringVar()
		Label(self, text=name).pack(side=LEFT)
		cb = Pmw.ComboBox(self, entry_textvariable=self.tkvar)
		cb.setlist(choices)
		cb.pack(side=LEFT)

	def arg_boolean(self, name):
		self.tkvar = IntVar()
		Checkbutton(self, text=name, variable=self.tkvar).pack(side=LEFT)

	def arg_integer(self, name):
		self.tkvar = IntVar()
		Label(self, text=name).pack(side=LEFT)
		Entry(self, textvariable=self.tkvar, width=10).pack(side=LEFT)

	def arg_float(self, name):
		self.tkvar = DoubleVar()
		Label(self, text=name).pack(side=LEFT)
		Entry(self, textvariable=self.tkvar, width=10).pack(side=LEFT)

	def arg_string(self, name):
		self.tkvar = StringVar()
		Label(self, text=name).pack(side=LEFT)
		Entry(self, textvariable=self.tkvar, width=10).pack(side=LEFT)

	def arg_array(self, name):
		raise NotImplementedError

	def arg_struct(self, name, struct):
		sc = TreeWidget.ScrolledCanvas(self, bg='white', highlightthickness=0)
		sc.frame.pack()
		item = StructTreeItem(name, struct)
		node = TreeWidget.TreeNode(sc.canvas, None, item)
		node.update()
		
	def arg_date(self, name):
		raise NotImplementedError

	def arg_binary(self, name):
		raise NotImplementedError


class NodeGUIComponent(Frame):
	def __init__(self, parent, clientcomponent):
		Frame.__init__(self, parent)
		self['bd'] = 3
		self['relief'] = SOLID
		self.client = clientcomponent
		self.args = {}
		self.__build()

	def __build(self):
		name = self.client.name


		for argname in self.client.argnames():
			argtype = self.client.argtype(argname)
			argvalue = self.client.argvaluesdict[argname]
			argalias = self.client.argaliasdict[argname]
			a = NodeGUIArg(self, argname, argalias, argtype, argvalue)
			a.pack()
			self.args[argname] = a

		def butcom():
			for key,value in self.args.items():
				self.client.setarg(key, self.args[key].get())
			ret = self.client.execute()
			self.process_return(ret)

		but = Button(self, text=name, command=butcom)
		but.pack()

		retwidget = self.init_return(self.client.returntype)
		if retwidget is not None:
			retwidget.pack()

	def process_return(self, returnvalue):
		ret = self.returntype
		if ret in ('array','string'):
			self.retwidget['state'] = NORMAL
			self.retwidget.delete(1.0,END)
			self.retwidget.insert(1.0, `returnvalue`)
			self.retwidget['state'] = DISABLED
		if ret == 'struct':
			self.retwidget['state'] = NORMAL
			self.retwidget['height'] = len(returnvalue)
			self.retwidget.delete(1.0,END)
			for key,value in returnvalue.items():
				rowstr = key + ': ' + `value` + '\n'
				self.retwidget.insert(END, rowstr)
			self.retwidget['state'] = DISABLED
		else:
			pass

	def init_return(self, returntype):
		'''
		set up for handling return values
		return a widget if one was created
		'''
		self.returntype = returntype
		if returntype in ('array','string','struct'):
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
		self.id = self.uiclient.execute('ID')
		self.components = {}
		self.__build()

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
		
class StructTreeItem(TreeWidget.TreeItem):
	def __init__(self, key, value):
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
		self.value = type(self.value)(text)

	def GetIconName(self):
		pass

	def IsExpandable(self):
		if self.key:
			return True
		else:
			return False

	def GetSubList(self):
		if type(self.value) is dict:
			sublist = []
			for k in self.value:
				item = StructTreeItem(k, self.value[k])
				sublist.append(item)
			return sublist
		else:
			return [StructTreeItem(None, self.value)]

#class StructTreeItem(TreeWidget.TreeItem):
#	def __init__(self, key, value):
#		self.key = key
#		self.value = value
#
#	def GetText(self):
#		if self.key:
#			return self.key
#		else:
#			return self.value
#
#	def IsEditable(self):
#		if self.key:
#			return False
#		else:
#			return True
#
#	def SetText(self):
#		pass
#
#	def GetIconName(self):
#		pass
#
#	def IsExpandable(self):
#		return type(self.value) is dict
#
#	def GetSubList(self):
#		if type(self.value) is dict:
#			sublist = []
#			for k in self.value:
#				item = StructTreeItem(k, self.value[k])
#				sublist.append(item)
#			return sublist
#		else:
#			return [StructTreeItem(None, self.value)]

if __name__ == '__main__':
	import sys

	tk = Tk()
	hostname = sys.argv[1]
	port = sys.argv[2]
	gui = NodeGUI(tk, sys.argv[1], sys.argv[2])
	newtitle = 'Interface to %s' % gui.id
	tk.wm_title(newtitle)
	gui.pack()
	tk.mainloop()
