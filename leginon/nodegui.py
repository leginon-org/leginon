#!/usr/bin/env python

from Tkinter import *
import Pmw
import interface

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
		elif argtype == 'struct':
			self.arg_struct(argalias)
		elif argtype == 'date':
			self.arg_date(argalias)
		elif argtype == 'binary':
			self.arg_binary(argalias)
		elif type(argtype) in (list,tuple):
			self.arg_choice(argalias, argtype)
		else:
			raise RuntimeError('argtype not supported')

		## sets the initial value
		if argvalue:
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
		self.tkvar = FloatVar()
		Label(self, text=name).pack(side=LEFT)
		Entry(self, textvariable=self.tkvar, width=10).pack(side=LEFT)

	def arg_string(self, name):
		self.tkvar = StringVar()
		Label(self, text=name).pack(side=LEFT)
		Entry(self, textvariable=self.tkvar, width=10).pack(side=LEFT)

	def arg_array(self, name):
		raise NotImplementedError

	def arg_struct(self, name):
		raise NotImplementedError
		
	def arg_date(self, name):
		raise NotImplementedError

	def arg_binary(self, name):
		raise NotImplementedError


class NodeGUIComponent(Frame):
	def __init__(self, parent, clientcomponent):
		Frame.__init__(self, parent)
		self['bd'] = 4
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
			print ret

		but = Button(self, text=name, command=butcom)
		but.pack()


class NodeGUI(Frame):
	def __init__(self, parent, hostname, port):
		Frame.__init__(self, parent)
		self.uiclient = interface.Client(hostname, port)
		self.id = self.uiclient.id
		self.components = {}
		self.__build()

	def __build(self):
		b=Button(self, text='Refresh', command=self.__build_components)
		b.pack(side=TOP)
		self.__build_components()

	def __build_components(self):
		## destroy components if this is a refresh
		for value in self.components.values():
			value.destroy()
		self.components.clear()

		self.uiclient.getMethods()
			
		for key,value in self.uiclient.funcdict.items():
			c = NodeGUIComponent(self, value)
			c.pack(side=TOP, expand=YES, fill=BOTH)
			self.components[key] = c
		

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
