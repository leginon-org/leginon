#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import node
import application
import uidata
import data

class ApplicationEditor(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.application = application.Application(self)
		self.defineUserInterface()
		self.start()

	def uiSave(self):
		self.logger.info('Saving application...')
		applicationdata = self.applicationeditor.get()
		self.logger.info('Application data %s' % applicationdata)
		self.application.setName(applicationdata['name'])
		self.application.clear()
		for nodespec in applicationdata['nodes']:
			self.logger.info('Adding node spec %s' % nodespec)
			apply(self.application.addNodeSpec, nodespec)
		for bindingspec in applicationdata['bindings']:
			self.logger.info('Adding bind spec %s' % bindspec)
			apply(self.application.addBindingSpec, bindingspec)
		self.application.save()
		self.logger.info('Application saved')

	def uiUpdate(self):
		applicationdatalist = self.research(dataclass=data.ApplicationData)
		applicationnamelist = []
		for applicationdata in applicationdatalist:
			name = applicationdata['name']
			if name not in applicationnamelist:
				applicationnamelist.append(name)
		self.uiapplicationlist.set(applicationnamelist, 0)

	def uiLoad(self):
		name = self.uiapplicationlist.getSelectedValue()
		if name is None:
			return
		self.application.clear()
		self.application.load(name)
		applicationdata = {'name': name, 'nodes': [], 'bindings': []}
		for nodespecdata in self.application.nodespecs:
			applicationdata['nodes'].append((nodespecdata['class string'],
																				nodespecdata['alias'],
																				nodespecdata['launcher alias'],
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
		self.uiapplicationlist = uidata.SingleSelectFromList('Application', [], 0)
		self.uiUpdate()
		update = uidata.Method('Refresh', self.uiUpdate)
		load = uidata.Method('Load', self.uiLoad)
		container = uidata.LargeContainer('Application Editor')
		container.addObjects((self.applicationeditor, save, self.uiapplicationlist, update, load))
		self.uicontainer.addObject(container)

