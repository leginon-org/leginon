#!/usr/bin/env python

import node
import data
import event
import nodeclassreg
import calllauncher
import time
import threading
import sys


class Launcher(node.Node):
	def __init__(self, id, nodelocations = {}, port = None, **kwargs):
		node.Node.__init__(self, id, 'launcher session', nodelocations, tcpport=port, **kwargs)
		self.checkPythonVersion()
		self.addEventInput(event.LaunchEvent, self.handleLaunch)
		self.addEventOutput(event.NodeClassesPublishEvent)
		self.caller = calllauncher.CallLauncher()
		l = self.location()
		print 'launcher id: %s, at hostname: %s, TCP: %s, UI: %s' % (self.id,
															l['hostname'], l['TCP port'], l['UI port'])
		#self.print_location()
		self.defineUserInterface()
#		self.start()

	def addManager(self, loc):
		node.Node.addManager(self, loc)
		time.sleep(1)
		self.publishNodeClasses()
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))

	def start(self):
		self.main()
		self.die_event.wait()
		self.outputEvent(event.NodeUninitializedEvent(id=self.ID()))
		self.exit()

	def main(self):
		pass

	def publishNodeClasses(self):
		#reload(nodeclassreg)
		nodeclassnames = nodeclassreg.getNodeClassNames()
		d = data.NodeClassesData(id=self.ID(), nodeclasses=nodeclassnames)
		self.publish(d, pubevent=True)

	def handleLaunch(self, launchevent):
		# unpack event
		newproc = launchevent['newproc']
		targetclass = launchevent['targetclass']
		args = launchevent['args']
		if launchevent['kwargs'] is not None:
			kwargs = launchevent['kwargs']
		else:
			kwargs = {}

		# get the requested class object
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		print 'launching', nodeclass

		## thread or process
		if newproc:
			self.caller.launchCall('fork',nodeclass, args,kwargs)
		else:
			self.caller.launchCall('thread',nodeclass, args,kwargs)
		self.confirmEvent(launchevent)

	def launchThread(self):
		pass

	def launchProcess(self):
		pass

if __name__ == '__main__':
	import sys, socket

	myhost = socket.gethostname()
	myid = (myhost,)

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['TCP port'] = int(sys.argv[2])
			#managerlocation['UNIX pipe filename'] = str(sys.argv[3])
			m = Launcher(myid, {'manager': managerlocation})
		except IndexError:
			m = Launcher(myid, {}, int(sys.argv[1]))
	except IndexError:
		try:
			m = Launcher(myid, {}, 55555)
		except:
			m = Launcher(myid, {})
	m.start()

