#!/usr/bin/env python

import signal
import node, data
import event
import threading
import nodeclassreg
import calllauncher
import time


class Launcher(node.Node):
	def __init__(self, id, managerlocation = None):
		node.Node.__init__(self, id, managerlocation)

		self.addEventInput(event.LaunchEvent, self.handleLaunch)
		self.addEventInput(event.UpdateNodeClassesEvent, self.publishNodeClasses)
		self.addEventOutput(event.NodeClassesPublishEvent)
		self.caller = calllauncher.CallLauncher()
		print 'launcher id: %s' % (self.id,)

		self.start()

	def addManager(self, loc):
		'''
		Node uses NodeAvailableEvent 
		This uses LauncherAvailableEvent
		'''
		self.managerloc = loc
		self.addEventClient(('manager',), loc)

		launcherinfo = self.location()
		e = event.LauncherAvailableEvent(self.ID(), launcherinfo)
		self.outputEvent(ievent=e, wait=1)
		time.sleep(1)
		self.publishNodeClasses()

	def main(self):
		pass

	def publishNodeClasses(self):
		reload(nodeclassreg)
		print 'publishNodeClasses'
		nodeclassnames = nodeclassreg.getNodeClassNames()
		print 'nodeclassnames', nodeclassnames
		d = data.NodeClassesData(self.ID(), nodeclassnames)
		print 'DDDD content', d.content
		self.publish(d, event.NodeClassesPublishEvent)

	def handleLaunch(self, launchevent):
		# unpack event content
		newproc = launchevent.content['newproc']
		targetclass = launchevent.content['targetclass']
		args = launchevent.content['args']
		kwargs = launchevent.content['kwargs']

		# get the requested class object
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		## thread or process
		if newproc:
			self.caller.launchCall('fork',nodeclass,args,kwargs)
		else:
			self.caller.launchCall('thread',nodeclass,args,kwargs)

	def defineUserInterface(self):
		nint = node.Node.defineUserInterface(self)

		ref = self.registerUIMethod(self.uiRefresh, 'Refresh', ())

		self.registerUISpec('Launcher: %s' % self.id, (nint, ref))

	def uiRefresh(self):
		self.publishNodeClasses()
		return ''

	def launchThread(self):
		pass

	def launchProcess(self):
		pass

#	def launchNode(self, nodeid, nodeclass, args = None):
#		## new node's manager = launcher's manager
#		print 'launching %s %s' % (nodeid, nodeclass)
#		nodeargs = tuple([nodeid, self.managerloc] + list(args))
#		apply(nodeclass, nodeargs)
#
#	def launchDataServer(self, dataserverclass):
#		print 'launching %s' % nodeclass
#		dataserverclass()


if __name__ == '__main__':
	import sys,socket

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['TCP port'] = int(sys.argv[2])
#	manloc['UNIX pipe filename'] = str(sys.argv[3])

	myhost = socket.gethostname()
	myid = (myhost,)

	m = Launcher(myid, manloc)
