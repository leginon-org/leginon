#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

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
		initializer = {'name': 'launcher session'}
		session = data.SessionData(initializer=initializer)
		node.Node.__init__(self, id, session, nodelocations, tcpport=port, **kwargs)
		self.addEventInput(event.LaunchEvent, self.handleLaunch)
		self.caller = calllauncher.CallLauncher()
		self.defineUserInterface()
#		l = self.location()
#		self.start()

	def addManager(self, location):
		node.Node.addManager(self, location)
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

		#print 'launching', nodeclass

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

	print 'Launcher initializing...',
	myhost = socket.gethostname()
	myid = (myhost,)

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['data transport'] = {}
			managerlocation['data transport']['TCP transport'] = {}
			port = int(sys.argv[2])
			managerlocation['data transport']['TCP transport']['port'] = port
			m = Launcher(myid, {'manager': managerlocation})
		except IndexError:
			m = Launcher(myid, {}, int(sys.argv[1]))
	except IndexError:
		try:
			m = Launcher(myid, {}, 55555)
		except:
			m = Launcher(myid, {})
	print 'Done.'
	m.start()

