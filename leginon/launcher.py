#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
from databinder import DataBinder
import event
import leginonobject
import node
import nodeclassreg
import uiserver

class Launcher(node.Node):
	def __init__(self, id, session=None, tcpport=None, xmlrpcport=None, **kwargs):
		self.nodes = []

		self.initializeLogger(id[-1])

		node.Node.__init__(self, id, session, tcpport=tcpport, xmlrpcport=xmlrpcport, **kwargs)

		#self.datahandler.insert(uicontainer)

		self.defineUserInterface()
		self.addEventInput(event.CreateNodeEvent, self.onCreateNode)
		self.start()

	def defineUserInterface(self):
		#self.initializeLoggerUserInterface()
		node.Node.defineUserInterface(self)

	def start(self):
		pass

	def exitNodes(self):
		for n in list(self.nodes):
			n.exit()

	def setManager(self, location):
		self.exitNodes()
		self.uicontainer.sesssion = self.session
		node.Node.setManager(self, location)
		self.publishNodeClasses()
		self.outputEvent(event.NodeInitializedEvent(node=self.id))

	def exit(self):
		self.exitNodes()
		node.Node.exit(self)
		self.server.exit()

	def publishNodeClasses(self):
		#reload(nodeclassreg)
		nodeclassnames = nodeclassreg.getNodeClassNames()
		d = data.NodeClassesData(nodeclasses=nodeclassnames)
		self.publish(d, pubevent=True)

	def onCreateNode(self, ievent):
		targetclass = ievent['targetclass']
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		nodeid = ievent['node']
		session = ievent['session']
		managerlocation = ievent['manager location']

		kwargs = {}
		kwargs['otheruiserver'] = self.uiserver
		kwargs['launcher'] = self
		kwargs['otherdatabinder'] = self.databinder

		self.nodes.append(nodeclass(nodeid, session, managerlocation, **kwargs))
		self.confirmEvent(ievent)

	def onDestroyNode(self, node):
		self.nodes.remove(node)

if __name__ == '__main__':
	import socket
	import sys
	import time

	print 'Launcher initializing...',
	hostname = socket.gethostname().lower()
	launcherid = (hostname,)

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['data binder'] = {}
			managerlocation['data binder']['TCP transport'] = {}
			port = int(sys.argv[2])
			managerlocation['data binder']['TCP transport']['port'] = port
			launcher = Launcher(launcherid, managerlocation=managerlocation)
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

