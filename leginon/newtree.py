import Tree
import Tkinter

class EntryTree(Tkinter.Frame):
	def __init__(self, parent, value, name='', **kwargs):
		Tkinter.Frame.__init__(self, parent, **kwargs)
		self.value = value
		self.editvariable = Tkinter.StringVar()
		self.editentry = Tkinter.Entry(self, textvariable=self.editvariable)
		self.editentry.bind('<KeyPress-Return>', self.enterCallback)
		self.name = name
		self.edit_tree = EditTree(self, value, self.name, self.get_contents, self.editvariable, bg='white', bd=1, relief=Tkinter.SUNKEN, height=180, width=200)
#		self.edit_tree = EditTree(self, value, self.name, self.get_contents, self.editvariable, bg='white', bd=1, relief=Tkinter.SUNKEN)
		self.edit_tree.grid(row=0, column=0, sticky='nsew')
		self.sb1 = Tkinter.Scrollbar(self)
		self.sb1.grid(row=0, column=1, sticky='ns')
		self.edit_tree.configure(yscrollcommand=self.sb1.set)
		self.sb1.configure(command=self.edit_tree.yview)

		self.sb2 = Tkinter.Scrollbar(self, orient=Tkinter.HORIZONTAL)
		self.sb2.grid(row=1, column=0, sticky='ew')
		self.edit_tree.configure(xscrollcommand=self.sb2.set)
		self.sb2.configure(command=self.edit_tree.xview)

		self.edit_tree.root.expand()
		self.editentry.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)

	def get_contents(self, node):
		content = node.id
		if type(node.id) is dict:
			keys = node.id.keys()
			keys.sort()
			for key in keys:
				node.widget.add_node(name=key, id=node.id[key], flag=True)
		else:
			node.widget.add_node(name=node.id, id=node.id, flag=False)

	def enterCallback(self, ievent=None):
		valuetype = type(self.edit_tree.pos.id)
		if valuetype is str:
			value = self.editvariable.get()
		else:
			value = eval(self.editvariable.get())
		if type(value) == valuetype:
			node = self.edit_tree.pos
			node.id = value
			node.set_label(value)
			self.edit_tree.move_cursor(node)
			node.parent_node.parent_node.id[node.parent_node.get_label()] = value

	def get(self):
		return self.value

	def set(self, value):
		self.editvariable.set('')
		self.edit_tree.destroy()
		self.value = value
		self.edit_tree = EditTree(self, value, self.name, self.get_contents, self.editvariable, bg='white', bd=1, relief=Tkinter.SUNKEN, height=180, width=200)
		#self.edit_tree = EditTree(self, value, self.name, self.get_contents, self.editvariable, bg='white', bd=1, relief=Tkinter.SUNKEN)
		self.edit_tree.grid(row=0, column=0, sticky='nsew')
		self.edit_tree.configure(yscrollcommand=self.sb1.set)
		self.sb1.configure(command=self.edit_tree.yview)
		self.edit_tree.configure(xscrollcommand=self.sb2.set)
		self.sb2.configure(command=self.edit_tree.xview)
		self.edit_tree.root.expand()

#	def set(self, value):
#		self.editvariable.set('')
#		self.edit_tree.root.collapse()
#		self.value = value
#		self.edit_tree.root.expand()

	def printNode(self, node):
		print 'node =', node, 'label =', node.get_label(), 'value =', node.id
		if node.expandable():
			node.expand()
		if node.child_nodes:
			for child in node.child_nodes:
				self.printNode(child)

	def setNode2(self, node, value):
		if type(value) is dict:
			for key in node.id:
				if key in value:
					if node.expandable() and not node.expanded():
						node.expand()
					for child in node.child_nodes:
						if child.get_label() == key:
							self.setNode(child, value[key])
				else:
					for child in node.child_nodes:
						if child.get_label() == key:
							child.delete()
			for key in value:
				if key not in node.id:
					node.widget.add_node(name=key, id=value[key], flag=True)
					node.expand()
		else:
			node.expand()
			node.child_nodes[0]
			print node, node.get_label(), node.id, value
		node.id = value

class EditTree(Tree.Tree):
	def __init__(self, master, root_id, root_label, get_contents_callback, editvariable, **kwargs):
		self.editvariable = editvariable
		Tree.Tree.__init__(self, master, root_id, root_label, get_contents_callback, **kwargs)

	def move_cursor(self, node):
		if hasattr(self, 'pos'):
			if node != self.pos:
				self.editvariable.set('')
		Tree.Tree.move_cursor(self, node)
		if not node.expandable_flag:
			self.editvariable.set(str(self.pos.id))
			print type(self.pos.id), self.pos.id

if __name__ == '__main__':

	root = Tkinter.Tk()
	tree1 = {'a': {'c': 1, 'd': {'x': 77, 'y': 88}}, 'q': 2, 'n': {'1': 1.0, '2': 2.0}}
	tree2 = {'a': {'c': 5, 'd': 'faskdjfkalsd'}, 'm': 6, 'u': {'1': 5.0, '2': 6.0}}

	t=EntryTree(root, tree1)
	print t.value == tree1
	import copy
	t.set(copy.deepcopy(tree2))
	print t.value
	print t.value == tree2
	t.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)

	root.mainloop()
