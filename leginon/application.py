import data
import event
import time
import threading
import leginonobject

class Application(leginonobject.LeginonObject):
	def __init__(self, id, node, name=None):
		leginonobject.LeginonObject.__init__(self, id)
		self.node = node
		self.data = data.ApplicationData()
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []
		self.launcherids = {}
		self.nodeids = {}

	def clear(self):
		name = self.getName()
		self.data = data.ApplicationData()
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []
		self.launcherids = {}
		self.nodeids = {}

	def getName(self):
		return self.data['name']

	def setName(self, name):
		self.data['name'] = name

	def addNodeSpec(self, class_string, alias, launcheralias,
									args=(), npf=0, dependencies=[]):
		for spec in self.nodespecs:
			if alias == spec['alias']:
				self.nodespecs.remove(spec)
				break
		nodespecdata = data.NodeSpecData()
		nodespecdata['class string'] = class_string
		nodespecdata['alias'] = alias
		nodespecdata['launcher alias'] = launcheralias
		nodespecdata['args'] = args
		nodespecdata['new process flag'] = npf
		nodespecdata['dependencies'] = dependencies
		nodespecdata['application'] = self.data
		self.nodespecs.append(nodespecdata)

	def getLauncherAliases(self):
		aliases = []
		for nodespecdata in self.nodespecs:
			if nodespecdata['launcher alias'] not in aliases:
				aliases.append(nodespecdata['launcher alias'])
		return aliases

	def setLauncherAlias(self, alias, id):
		self.launcherids[alias] = id

	def delNodeSpec(self, alias):
		for nodespec in self.nodespecs:
			if nodespec['alias'] == alias:
				self.nodespecs.remove(nodespec)

	def addBindingSpec(self, eventclass_string, fromnodealias, tonodealias):
		bindingspecdata = data.BindingSpecData()
		bindingspecdata['event class string'] = eventclass_string
		bindingspecdata['from node alias'] = fromnodealias
		bindingspecdata['to node alias'] = tonodealias
		bindingspecdata['application'] = self.data
		for spec in self.bindingspecs:
			same = True
			for key in bindingspecdata:
				if bindingspecdata[key] != spec[key]:
					same = False
			if same:
				raise ValueError('binding already exists in application')
		self.bindingspecs.append(bindingspecdata)

	def delBindingSpec(self, eventclass_string, fromnodealias, tonodealias):
		bindingspecdata = data.BindingSpecData()
		bindingspecdata['event class string'] = eventclass_string
		bindingspecdata['from node alias'] = fromnodealias
		bindingspecdata['to node alias'] = tonodealias
		bindingspecdata['application'] = self.data
		for spec in self.bindingspecs:
			same = True
			for key in bindingspecdata:
				if bindingspecdata[key] != spec[key]:
					same = False
			if same:
				self.bindingspecs.remove(spec)

	def getNodeIDFromAlias(self, alias):
		try:
			return self.nodeids[alias]
		except KeyError:
			raise ValueError('No such node alias mapped to ID')

	def getLauncherIDFromAlias(self, alias):
		try:
			return self.launcherids[alias]
		except KeyError:
			raise ValueError('No such launcher alias mapped to ID')

	def nodeSpec2Args(self, ns):
		try:
			launcherid = self.getLauncherIDFromAlias(ns['launcher alias'])
		except ValueError:
			raise ValueError('Invalid node specification')
		nodename = self.getName() + ' ' + ns['alias']
		args = tuple(ns['args'])
		return ns['alias'], (launcherid, ns['new process flag'],
													ns['class string'], nodename, args,
													ns['dependencies'])

	def bindingSpec2Args(self, bs):
		# i know...
		try:
			eventclass = eval('event.' + bs['event class string'])
		except:
			raise ValueError('cannot get event class for binding')
		try:
			fromnodeid = self.getNodeIDFromAlias(bs['from node alias'])
			tonodeid = self.getNodeIDFromAlias(bs['to node alias'])
		except ValueError:
			raise ValueError('Invalid binding specification')
		return (eventclass, fromnodeid, tonodeid)

	def launch(self):
		if not hasattr(self.node, 'addEventDistmap'):
			raise RuntimeError('Application node unable to launch')
		threads = []
		for nodespec in self.nodespecs:
			alias, args = self.nodeSpec2Args(nodespec)
			id = self.launchNode(args)
			self.launchednodes.append(id)
			self.nodeids[alias] = id
		for bindingspec in self.bindingspecs:
			args = self.bindingSpec2Args(bindingspec)
			self.printerror('binding %s' % str(args))
			apply(self.node.addEventDistmap, args)

	def launchNode(self, args):
		if not hasattr(self.node, 'launchNode'):
			raise RuntimeError('Application node unable to launch node')
		self.printerror('launching %s' % str(args))
		newid = apply(self.node.launchNode, args)
		return newid

	def kill(self):
		if not hasattr(self.node, 'killNode'):
			raise RuntimeError('Application node unable to kill')
		while self.launchednodes:
			nodeid = self.launchednodes.pop()
			self.printerror('killing %s' % (nodeid,))
			try:
				self.node.killNode(nodeid)
			except:
				self.printException()
		self.nodeids = {}

	def save(self):
		self.data['version'] = self.getNewVersion(self.data['name'])
		self.node.publish(self.data, database=True)
		for nodespecdata in self.nodespecs:
			self.node.publish(nodespecdata, database=True)
		for bindingspecdata in self.bindingspecs:
			self.node.publish(bindingspecdata, database=True)

	def getNewVersion(self, name):
		instance = data.ApplicationData(name=name)
		applicationdatalist = self.node.research(datainstance=instance)
		try:
			applicationdata = applicationdatalist[0]
		except IndexError:
			return 0
		return applicationdata['version'] + 1

	def load(self, name):
		instance = data.ApplicationData(name=name)
		applicationdatalist = self.node.research(datainstance=instance)
		try:
			self.data = applicationdatalist[0]
		except IndexError:
			raise ValueError('no such application')
		nodeinstance = data.NodeSpecData(application=self.data)
		self.nodespecs = self.node.research(datainstance=nodeinstance)
		bindinginstance = data.BindingSpecData(application=self.data)
		self.bindingspecs = self.node.research(datainstance=bindinginstance)

