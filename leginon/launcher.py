#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import datatransport
import event
import leginonobject
import node
import nodeclassreg
#import time
import uiserver

class Launcher(node.Node):
	def __init__(self, id, session=None, tcpport=None, xmlrpcport=None, **kwargs):
		self.nodes = []

		self.uicontainer = uiserver.Server(str(id[-1]), xmlrpcport)

		self.datahandler = node.DataHandler(self)
		self.server = datatransport.Server(self.datahandler, tcpport)

		node.Node.__init__(self, id, session, **kwargs)

		self.datahandler.insert(self.uicontainer)

		self.defineUserInterface()
		self.addEventInput(event.CreateNodeEvent, self.onCreateNode)
		self.start()

	def start(self):
		pass

	def exitNodes(self):
		for n in list(self.nodes):
			n.exit()

	def setManager(self, location):
		self.exitNodes()
		node.Node.setManager(self, location)
		self.publishNodeClasses()
		self.outputEvent(event.NodeInitializedEvent(id=self.ID()))

	def exit(self):
		self.exitNodes()
		node.Node.exit(self)
		self.server.exit()

	def location(self):
		location = leginonobject.LeginonObject.location(self)
		location['data transport'] = self.server.location()
		location['UI'] = self.uicontainer.location()
		return location

	def publishNodeClasses(self):
		#reload(nodeclassreg)
		nodeclassnames = nodeclassreg.getNodeClassNames()
		d = data.NodeClassesData(id=self.ID(), nodeclasses=nodeclassnames)
		self.publish(d, pubevent=True)

	def onCreateNode(self, ievent):
		targetclass = ievent['targetclass']
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		nodeid = ievent['node ID']
		session = ievent['session']
		nodelocations = ievent['node locations']

		kwargs = {}
		kwargs['uicontainer'] = self.uicontainer
		kwargs['launcher'] = self
		kwargs['datahandler'] = self.datahandler

		self.nodes.append(nodeclass(nodeid, session, nodelocations, **kwargs))
		self.confirmEvent(ievent)

	def onDestroyNode(self, node):
		self.nodes.remove(node)

if __name__ == '__main__':
	import socket
	import sys
	import time

	print 'Launcher initializing...',
	hostname = socket.gethostname()
	launcherid = (hostname,)

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['data transport'] = {}
			managerlocation['data transport']['TCP transport'] = {}
			port = int(sys.argv[2])
			managerlocation['data transport']['TCP transport']['port'] = port
			launcher = Launcher(launcherid,
													nodelocations={'manager': managerlocation})
		except IndexError:
			launcher = Launcher(launcherid, tcpport=int(sys.argv[1]))
	except IndexError:
		try:
			launcher = Launcher(launcherid, tcpport=55555)
		except:
			launcher = Launcher(launcherid)
	print 'Done.'
	print 'Press control-c to exit'
	launcher.start()
	try:
		while True:
			time.sleep(0.5)
	except KeyboardInterrupt:
		pass
	print 'Launcher exiting...',
	launcher.exit()
	print 'Done.'

