'''
This is an Application manager to be included as a component of Manager
'''
import data
import event
import time
import threading
import leginonobject

class Application(leginonobject.LeginonObject):
	def __init__(self, id, manager, name=None):
		leginonobject.LeginonObject.__init__(self, id)
		self.manager = manager
		self.data = data.ApplicationData(id=self.ID())
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []

	def setName(self, name):
		self.data['name'] = name

	def addNodeSpec(self, class_string, name, launcherid,
									args=(), npf=0, dependencies=[]):
		for spec in self.nodespecs:
			if name == spec['name']:
				raise ValueError('node already exists in application')
		nodespecdata = data.NodeSpecData()
		nodespecdata['class string'] = class_string
		nodespecdata['name'] = name
		nodespecdata['launcher ID'] = launcherid
		nodespecdata['args'] = args
		nodespecdata['new process flag'] = npf
		nodespecdata['dependencies'] = dependencies
		nodespecdata['application'] = self.data
		self.nodespecs.append(nodespecdata)

	def delNodeSpec(self, name):
		for nodespec in self.nodespecs:
			if nodespec['name'] == name:
				self.nodespecs.remove(nodespec)

	def addBindingSpec(self, eventclass_string, fromnodeid, tonodeid):
		bindingspecdata = data.BindingSpecData()
		bindingspecdata['event class string'] = eventclass_string
		bindingspecdata['from node ID'] = fromnodeid
		bindingspecdata['to node ID'] = tonodeid
		bindingspecdata['application'] = self.data
		for spec in self.bindingspecs:
			same = True
			for key in bindingspecdata:
				if bindingspecdata[key] != spec[key]:
					same = False
			if same:
				raise ValueError('binding already exists in application')
		self.bindingspecs.append(bindingspecdata)

	def delBindingSpec(self, eventclass_string, fromnode, tonode):
		bindingspecdata = data.BindingSpecData()
		bindingspecdata['event class string'] = eventclass_string
		bindingspecdata['from node ID'] = fromnodeid
		bindingspecdata['to node ID'] = tonodeid
		bindingspecdata['application'] = self.data
		for spec in self.bindingspecs:
			same = True
			for key in bindingspecdata:
				if bindingspecdata[key] != spec[key]:
					same = False
			if same:
				self.bindingspec.remove(spec)

	def getLauncherIDs(self):
		launcherids = []
		for spec in self.nodespecs:
			launcherids.append(spec['launcher ID'])
		return launcherids

	def nodeSpec2Args(self, ns):
		return (ns['launcher ID'], ns['new process flag'], ns['class string'],
						ns['name'], tuple(ns['args']), ns['dependencies'], False)

	def bindingSpec2Args(self, bs):
		# i know...
		try:
			eventclass = eval('event.' + bs['event class string'])
		except:
			raise ValueError('cannot get event class for binding')
		return (eventclass, bs['from node ID'], bs['to node ID'], False)

	def launch(self):
		threads = []
		for nodespec in self.nodespecs:
			args = self.nodeSpec2Args(nodespec)
			self.launchNode(args)
		for bindingspec in self.bindingspecs:
			args = self.bindingSpec2Args(bindingspec)
			self.printerror('binding %s' % str(args))
			apply(self.manager.addEventDistmap, args)

	def launchNode(self, args):
			self.printerror('launching %s' % str(args))
			newid = apply(self.manager.launchNode, args)
			self.launchednodes.append(newid)

	def kill(self):
		while self.launchednodes:
			nodeid = self.launchednodes.pop()
			self.printerror('killing %s' % (nodeid,))
			try:
				self.manager.killNode(nodeid)
			except:
				self.printException()

	def save(self):
		self.manager.publish(self.data, database=True)
		for nodespecdata in self.nodespecs:
			self.manager.publish(nodespecdata, database=True)
		for bindingspecdata in self.bindingspecs:
			self.manager.publish(bindingspecdata, database=True)

	def load(self, name):
		instance = data.ApplicationData(name=name)
		applicationdatalist = self.manager.research(datainstance=instance)
		try:
			self.data = applicationdatalist[0]
		except IndexError:
			raise ValueError('no such application')
		instance['session'] = self.data['session']
		instance['id'] = self.data['id']
		nodeinstance = data.NodeSpecData(application=instance)
		self.nodespecs = self.manager.research(datainstance=nodeinstance)
		bindinginstance = data.BindingSpecData(application=instance)
		self.bindingspecs = self.manager.research(datainstance=bindinginstance)

