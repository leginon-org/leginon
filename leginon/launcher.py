#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import event
import leginonobject
import node
import nodeclassreg
import uiserver
import wxLauncher

class Launcher(node.Node):
	def __init__(self, name, session=None, tcpport=None, xmlrpcport=None, **kwargs):
		self.nodes = []

		self.initializeLogger(name)

		node.Node.__init__(self, name, session, tcpport=tcpport, xmlrpcport=xmlrpcport, **kwargs)

		self.addEventInput(event.CreateNodeEvent, self.onCreateNode)
		self.frame = wxLauncher.LauncherFrame(self)

	def start(self):
		pass

	def exitNodes(self):
		for n in list(self.nodes):
			n.exit()

	def setManager(self, location):
		self.exitNodes()
		node.Node.setManager(self, location)
		self.publishNodeClasses()
		self.outputEvent(event.NodeInitializedEvent(node=self.name))

	def exit(self):
		self.exitNodes()
		node.Node.exit(self)

	def publishNodeClasses(self):
		#reload(nodeclassreg)
		nodeclassnames = nodeclassreg.getNodeClassNames()
		d = data.NodeClassesData(nodeclasses=nodeclassnames)
		self.publish(d, pubevent=True)

	def onCreateNode(self, ievent):
		targetclass = ievent['targetclass']
		nodeclass = nodeclassreg.getNodeClass(targetclass)

		nodename = ievent['node']
		session = ievent['session']
		managerlocation = ievent['manager location']

		kwargs = {}
		kwargs['otheruiserver'] = self.uiserver
		kwargs['launcher'] = self
		kwargs['otherdatabinder'] = self.databinder

		self.nodes.append(nodeclass(nodename, session, managerlocation, **kwargs))
		self.confirmEvent(ievent)

	def onDestroyNode(self, node):
		try:
			self.nodes.remove(node)
		except ValueError:
			pass # ???

if __name__ == '__main__':
	import socket
	import sys

	hostname = socket.gethostname().lower()
	launchername = hostname

	managerlocation = {}
	try:
		managerlocation['hostname'] = sys.argv[1]
		try:
			managerlocation['data binder'] = {}
			managerlocation['data binder']['TCP transport'] = {}
			port = int(sys.argv[2])
			managerlocation['data binder']['TCP transport']['port'] = port
			args, kwargs = (launchername,), {'managerlocation': managerlocation}
		except IndexError:
			args, kwargs = (launchername,), {'tcpport': int(sys.argv[1])}
	except IndexError:
		try:
			args, kwargs = (launchername,), {'tcpport': 55555}
			launcher = Launcher(launchername, tcpport=55555)
		except:
			args, kwargs = (launchername,), {}
	l = wxLauncher.LauncherApp(*args, **kwargs)
	l.MainLoop()

