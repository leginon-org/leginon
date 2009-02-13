#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import node
import nodeclassreg
from wx import PyDeadObjectError
import gui.wx.Launcher

class Launcher(node.Node):
	eventinputs = node.Node.eventinputs + [event.CreateNodeEvent,
																					event.NodeOrderEvent]
	def __init__(self, name, session=None, **kwargs):
		self.nodes = []
		node.Node.__init__(self, name, session, **kwargs)

		self.addEventInput(event.CreateNodeEvent, self.onCreateNode)
		self.addEventInput(event.NodeOrderEvent, self.onNodeOrder)

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
		d = leginondata.NodeClassesData(nodeclasses=nodeclassnames)
		self.publish(d, pubevent=True)

	def onNodeOrder(self, evt):
		self.panel.setOrder(evt['order'])

	def onCreateNode(self, ievent):
		targetclass = ievent['targetclass']
		try:
			nodeclass = nodeclassreg.getNodeClass(targetclass)
		except nodeclassreg.NotFoundError:
			self.confirmEvent(ievent, status='failed')
			return

		nodename = ievent['node']
		session = ievent['session']
		managerlocation = ievent['manager location']

		kwargs = {}
		kwargs['launcher'] = self
		kwargs['otherdatabinder'] = self.databinder

		if nodeclass.panelclass is not None:
			evt = gui.wx.Launcher.CreateNodePanelEvent(nodeclass.panelclass, nodename)
			self.panel.GetEventHandler().AddPendingEvent(evt)
			evt.event.wait()
			kwargs['panel'] = evt.panel

		n = nodeclass(nodename, session, managerlocation, **kwargs)
		self.nodes.append(n)

		evt = gui.wx.Launcher.CreateNodeEvent(n)
		self.panel.GetEventHandler().AddPendingEvent(evt)

		self.confirmEvent(ievent)

	def onDestroyNode(self, n):
		evt = gui.wx.Launcher.DestroyNodeEvent(n)
		try:
			self.panel.GetEventHandler().AddPendingEvent(evt)
		except PyDeadObjectError:
			pass

		try:
			self.nodes.remove(n)
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
		except:
			args, kwargs = (launchername,), {}
	l = gui.wx.Launcher.App(*args, **kwargs)
	print kwargs
	l.MainLoop()
	leginondata.datamanager.exit()

