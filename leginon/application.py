'''
This is an Application manager to be included as a component of Manager
'''
import shelve
import leginonobject

class Application(leginonobject.LeginonObject):
	def __init__(self, id, manager):
		leginonobject.LeginonObject.__init__(self, id)

		self.manager = manager
		self.launchspec = []
		self.bindspec = []

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

	def launch(self):
		for args in self.launchspec:
			apply(self.manager.launchNode, args)
		for args in self.bindspec:
			apply(self.manager.addEventDistmap, args)

	def kill(self):
		pass

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
