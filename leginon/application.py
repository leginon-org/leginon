#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#
import applications
import leginondata
import event

class Application(object):
	def __init__(self, node, name=None):
		self.node = node
		self.data = leginondata.ApplicationData()
		if name is not None:
			self.data['name'] = name
		self.nodespecs = []
		self.bindingspecs = []
		self.launchednodes = []
		self.launchernames = {}

	def clear(self):
		name = self.getName()
		self.data = leginondata.ApplicationData()
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
		nodespecdata = leginondata.NodeSpecData()
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
		bindingspecdata = leginondata.BindingSpecData()
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
		bindingspecdata = leginondata.BindingSpecData()
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
			raise ValueError('unmapped launcher alias')
		dependencies = []
		return (launchername, ns['class string'], ns['alias'], dependencies)

	def bindingSpec2Args(self, bs):
		try:
			eventclass = getattr(event, bs['event class string'])
		except:
			raise ValueError('cannot get event class for binding: %s' % (bs['event class string'],))
		try:
			fromnode = bs['from node alias']
			tonode = bs['to node alias']
		except ValueError:
			raise ValueError('invalid binding specification')
		return (eventclass, fromnode, tonode)

	def getNodeNames(self):
		if self.nodespecs is None:
			return []
		return map(lambda nsd: nsd['alias'], self.nodespecs)

	def launch(self):
		if not hasattr(self.node, 'addEventDistmap'):
			raise RuntimeError('application node unable to launch')
		threads = []
		for bindingspec in self.bindingspecs:
			args = self.bindingSpec2Args(bindingspec)
			#print 'binding %s' % str(args)
			apply(self.node.addEventDistmap, args)
		nodeclasses = map(lambda ns: (ns['alias'], ns['class string']),
											self.nodespecs)
		self.node.updateNodeOrder(nodeclasses)
		for nodespec in self.nodespecs:
			args = self.nodeSpec2Args(nodespec)
			name = self.launchNode(args)
			self.launchednodes.append(name)
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
			except Exception, e:
				print e

	def save(self):
		self.data['version'] = self.getNewVersion(self.data['name'])
		self.node.publish(self.data, database=True)
		for nodespecdata in self.nodespecs:
			self.node.publish(nodespecdata, database=True)
		for bindingspecdata in self.bindingspecs:
			self.node.publish(bindingspecdata, database=True)
		## create a copy so we can modify it
		self.data = leginondata.ApplicationData(initializer=self.data)

	def getNewVersion(self, name):
		instance = leginondata.ApplicationData(name=name)
		applicationdatalist = self.node.research(datainstance=instance)
		try:
			applicationdata = applicationdatalist[0]
		except IndexError:
			return 0
		return applicationdata['version'] + 1

	def load(self, name=None):
		if name is None:
			name = self.getName()
		if name in applications.builtin:
			self.load_built_in(name)
		else:
			self.load_from_db(name)

	def load_built_in(self, name):
		appdict = applications.builtin[name]
		self.applicationdata = self.data = appdict['application']
		self.nodespecs = appdict['nodes']
		self.bindingspecs = appdict['bindings']

	def load_from_db(self, name):
		instance = leginondata.ApplicationData(name=name)
		applicationdatalist = instance.query()
		try:
			appdata = applicationdatalist[0]
		except IndexError:
			raise ValueError('no such application')
		nodeinstance = leginondata.NodeSpecData(application=appdata)
		self.nodespecs = nodeinstance.query()
		bindinginstance = leginondata.BindingSpecData(application=appdata)
		self.bindingspecs = bindinginstance.query()
		self.applicationdata = appdata
		## create a copy so we can modify it
		self.data = leginondata.ApplicationData(initializer=appdata)
