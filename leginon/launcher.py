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
	def __init__(self, id, tcpport=None, xmlrpcport=None, **kwargs):
		initializer = {'name': 'launcher session'}
		session = data.SessionData(initializer=initializer)

		self.uicontainer = uiserver.Server(str(id[-1]), xmlrpcport)

		self.datahandler = node.DataHandler(self)
		self.server = datatransport.Server(self.datahandler, tcpport)

		node.Node.__init__(self, id, session, **kwargs)

		self.datahandler.insert(self.uicontainer)

		self.defineUserInterface()
		self.publishNodeClasses()
		self.addEventInput(event.CreateNodeEvent, self.onCreateNode)
		self.start()

	def exit(self):
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
		kwargs['launcher'] = self.id
		kwargs['datahandler'] = self.datahandler

		nodeclass(nodeid, session, nodelocations, **kwargs)
		self.confirmEvent(ievent)

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
			m = Launcher(myid, nodelocations={'manager': managerlocation})
		except IndexError:
			m = Launcher(myid, int(sys.argv[1]))
	except IndexError:
		try:
			m = Launcher(myid, 55555)
		except:
			m = Launcher(myid)
	print 'Done.'
	m.start()

