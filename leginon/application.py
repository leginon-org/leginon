'''
This is an Application manager to be included as a component of Manager
'''
import shelve
import leginonobject
import time
import os
import threading

class Application(leginonobject.LeginonObject):
	def __init__(self, id, manager):
		leginonobject.LeginonObject.__init__(self, id)
		self.manager = manager
		self.initApp()

	def initApp(self):
		self.launchspec = []
		self.bindspec = []
		self.launchednodeslock = threading.RLock()
		self.launchednodes = []

	def addLaunchSpec(self, args):
		if args not in self.launchspec:
			self.launchspec.append(args)

	def delLaunchSpec(self, args):
		if args in self.launchspec:
			self.launchspec.remove(args)

	def addBindSpec(self, args):
		if args not in self.bindspec:
			self.bindspec.append(args)

	def delBindSpec(self, args):
		if args in self.bindspec:
			self.bindspec.remove(args)

	def getLaunchers(self):
		launchers = []
		for args in self.launchspec:
			launchers.append(args[0])
		return launchers

	def launch(self):
		threads = []
		for args in self.launchspec:
			t = threading.Thread(name='launch %s thread' % str(args),
															target=self.launchNode, args=(args,))
			t.start()
			threads.append(t)
			print 'application sleep 0.5'
			time.sleep(0.5)
			print 'application sleep done'
			#print 'NEWID', newid
		for thread in threads:
			thread.join()
		for args in self.bindspec:
			self.printerror('binding %s' % str(args))
			apply(self.manager.addEventDistmap, args)

	def launchNode(self, args):
			self.printerror('launching %s' % str(args))
			newid = apply(self.manager.launchNode, args)
			self.launchednodeslock.acquire()
			self.launchednodes.append(newid)
			self.launchednodeslock.release()

	def kill(self):
		self.launchednodeslock.acquire()
		while self.launchednodes:
			nodeid = self.launchednodes.pop()
			self.printerror('killing %s' % (nodeid,))
			try:
				self.manager.killNode(nodeid)
			except:
				print 'error while killing %s' % (nodeid,)
		self.launchednodeslock.release()

	def save(self, filename):
		# for some reason updating after delLaunchSpec no worky
		try:
			os.remove(filename)
		except OSError:
			pass
		s = shelve.open(filename)
		s['launchspec'] = self.launchspec
		s['bindspec'] = self.bindspec
		s.close()

	def load(self, filename):
		s = shelve.open(filename)
		self.launchspec = s['launchspec']
		self.bindspec = s['bindspec']
		s.close()
