'''
This is an Application manager to be included as a component of Manager
'''
import shelve
import leginonobject

class Application(leginonobject.LeginonObject):
	def __init__(self, id, manager):
		leginonobject.LeginonObject.__init__(self, id)
		self.manager = manager
		self.initApp()

	def initApp(self):
		self.launchspec = []
		self.bindspec = []
		self.launchednodes = []

	def addLaunchSpec(self, args):
		if args not in self.launchspec:
			self.launchspec.append(args)

	def delLaunchSpec(self):
		pass

	def addBindSpec(self, args):
		if args not in self.bindspec:
			self.bindspec.append(args)

	def delBindSpec(self):
		pass

	def getLaunchers(self):
		launchers = []
		for args in self.launchspec:
			launchers.append(args[0])
		return launchers

	def launch(self):
		for args in self.launchspec:
			self.printerror('launching %s' % str(args))
			newid = apply(self.manager.launchNode, args)
			#print 'NEWID', newid
			self.launchednodes.append(newid)
		for args in self.bindspec:
			self.printerror('binding %s' % str(args))
			apply(self.manager.addEventDistmap, args)

	def kill(self):
		while self.launchednodes:
			nodeid = self.launchednodes.pop()
			self.printerror('killing %s' % (nodeid,))
			self.manager.killNode(nodeid)

	def save(self, filename):
		s = shelve.open(filename)
		s['launchspec'] = self.launchspec
		s['bindspec'] = self.bindspec
		s.close()

	def load(self, filename):
		s = shelve.open(filename)
		self.launchspec = s['launchspec']
		self.bindspec = s['bindspec']
		s.close()
