import node
import application
import uidata

class ApplicationEditor(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.application = application.Application(self.ID(), self)
		self.defineUserInterface()
		self.start()

	def uiSave(self):
		self.printerror('saving application')
		applicationdata = self.applicationeditor.get()
		print 'applicationdata =', applicationdata
		self.application.setName(applicationdata['name'])
		self.application.clear()
		for nodespec in applicationdata['nodes']:
			print 'adding nodespec', nodespec
			apply(self.application.addNodeSpec, nodespec)
		for bindingspec in applicationdata['bindings']:
			print 'adding bindspec', bindingspec
			apply(self.application.addBindingSpec, bindingspec)
		self.application.save()
		self.printerror('application saved')

	def uiLoad(self):
		applicationdata = self.applicationeditor.get()
		applicationdata['nodes'] = []
		applicationdata['bindings'] = []

		self.application.clear()
		self.application.load(applicationdata['name'])
		for nodespecdata in self.application.nodespecs:
			applicationdata['nodes'].append((nodespecdata['class string'],
																				nodespecdata['alias'],
																				nodespecdata['launcher alias'],
																				nodespecdata['args'],
																				nodespecdata['new process flag'],
																				nodespecdata['dependencies']))

		for bindingspecdata in self.application.bindingspecs:
			applicationdata['bindings'].append((bindingspecdata['event class string'],
																					bindingspecdata['from node alias'],
																					bindingspecdata['to node alias']))


		self.applicationeditor.set(applicationdata)

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		application = {'name': 'New Application', 'nodes': [], 'bindings': []}
		self.applicationeditor = uidata.Application('Application Editor',
																								application, 'rw')
		save = uidata.Method('Save', self.uiSave)
		load = uidata.Method('Load', self.uiLoad)
		container = uidata.MediumContainer('Application Editor')
		container.addObjects((self.applicationeditor, save, load))
		self.uiserver.addObject(container)

