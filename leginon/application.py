#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import data
import event

class Application(object):
	def __init__(self, node, name=None):
		self.node = node
		self.data = data.ApplicationData()
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []
		self.launchernames = {}

	def clear(self):
		name = self.getName()
		self.data = data.ApplicationData()
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []
		self.launchernames = {}

	def getName(self):
		return self.data['name']

	def setName(self, name):
		self.data['name'] = name

	def addNodeSpec(self, class_string, alias, launcheralias, dependencies=[]):
		for spec in self.nodespecs:
			if alias == spec['alias']:
				self.nodespecs.remove(spec)
				break
		nodespecdata = data.NodeSpecData()
		nodespecdata['class string'] = class_string
		nodespecdata['alias'] = alias
		nodespecdata['launcher alias'] = launcheralias
		nodespecdata['dependencies'] = dependencies
		nodespecdata['application'] = self.data
		self.nodespecs.append(nodespecdata)

	def getLauncherAliases(self):
		aliases = []
		for nodespecdata in self.nodespecs:
			if nodespecdata['launcher alias'] not in aliases:
				aliases.append(nodespecdata['launcher alias'])
		return aliases

	def setLauncherAlias(self, alias, name):
		self.launchernames[alias] = name

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

	def nodeSpec2Args(self, ns):
		try:
			launchername = self.launchernames[ns['launcher alias']]
		except KeyError:
			raise ValueError('Unmapped launcher alias')
		dependencies = []
		for dependency in ns['dependencies']:
			dependencies.append(dependency)
		return (launchername, ns['class string'], ns['alias'], dependencies)

	def bindingSpec2Args(self, bs):
		try:
			eventclass = getattr(event, bs['event class string'])
		except:
			raise ValueError('cannot get event class for binding')
		try:
			fromnode = bs['from node alias']
			tonode = bs['to node alias']
		except ValueError:
			raise ValueError('Invalid binding specification')
		return (eventclass, fromnode, tonode)

	def launch(self):
		if not hasattr(self.node, 'addEventDistmap'):
			raise RuntimeError('Application node unable to launch')
		threads = []
		for nodespec in self.nodespecs:
			args = self.nodeSpec2Args(nodespec)
			name = self.launchNode(args)
			self.launchednodes.append(name)
		for bindingspec in self.bindingspecs:
			args = self.bindingSpec2Args(bindingspec)
			#print 'binding %s' % str(args)
			apply(self.node.addEventDistmap, args)
		return self.launchednodes

	def launchNode(self, args):
		if not hasattr(self.node, 'launchNode'):
			raise RuntimeError('Application node unable to launch node')
		#print 'launching %s' % str(args)
		newname = apply(self.node.launchNode, args)
		return newname

	def kill(self):
		if not hasattr(self.node, 'killNode'):
			raise RuntimeError('Application node unable to kill')
		while self.launchednodes:
			nodename = self.launchednodes.pop()
			try:
				self.node.killNode(nodename)
			except:
				self.printException()

	def save(self):
		self.data['version'] = self.getNewVersion(self.data['name'])
		self.node.publish(self.data, database=True)
		for nodespecdata in self.nodespecs:
			self.node.publish(nodespecdata, database=True)
		for bindingspecdata in self.bindingspecs:
			self.node.publish(bindingspecdata, database=True)
		## create a copy so we can modify it
		self.data = data.ApplicationData(initializer=self.data)

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
			appdata = applicationdatalist[0]
		except IndexError:
			raise ValueError('no such application')
		nodeinstance = data.NodeSpecData(application=appdata)
		self.nodespecs = self.node.research(datainstance=nodeinstance)
		bindinginstance = data.BindingSpecData(application=appdata)
		self.bindingspecs = self.node.research(datainstance=bindinginstance)
		## create a copy so we can modify it
		self.data = data.ApplicationData(initializer=appdata)
