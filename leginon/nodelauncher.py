#!/usr/bin/env python

import signal
import node
import nodelib
import event
import threading


class NodeLauncher(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		self.addEventIn(event.LaunchNodeEvent, self.handleLaunchNode)
		self.main()

	def addManager(self):
		'''
		Node uses NodeReadyEvent 
		This uses NodeLauncherReadyEvent
		'''
		managerhost = self.managerloc['hostname']
		managerport = self.managerloc['event port']
		self.addEventClient('manager', managerhost, managerport)
		self.announce(event.NodeLauncherReadyEvent())

	def main(self):
		signal.pause()

	def handleLaunchNode(self, launchevent):
		print 'handling LaunchNodeEvent', launchevent
		print 'content', launchevent.content
		nodeid = launchevent.content['id']
		nodeclass = launchevent.content['class']
		myargs = (nodeid, nodeclass)
		print 'making thread'
		t = threading.Thread(target=self.launchNode, args=myargs)
		print 'setting daemon mode'
		t.setDaemon(1)
		print 'starting'
		t.start()

	def launchNode(self, nodeid, nodeclass):
		## new node's manager = launcher's manager
		print 'launching %s %s' % (nodeid, nodeclass)
		nodeclass(nodeid, self.managerloc)


if __name__ == '__main__':
	import sys,socket

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['event port'] = int(sys.argv[2])

	myhost = socket.gethostname()

	m = NodeLauncher(myhost, manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
