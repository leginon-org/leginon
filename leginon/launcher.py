#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright under
#       Apache License, Version 2.0
#       For terms of the license agreement
#       see  http://leginon.org
#

# testing before start
import configcheck
configcheck.testBeforeStart()

from leginon import leginondata
import event
import node
import noderegistry
from wx import PyDeadObjectError
import leginon.gui.wx.Launcher

class Launcher(node.Node):
	eventinputs = node.Node.eventinputs + [event.CreateNodeEvent,
																					event.NodeOrderEvent]
	def __init__(self, name, session=None, **kwargs):
		self.nodes = []
		self.order = [name,] # at least has itself
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
		nodeclassnames = noderegistry.getNodeClassNames()
		self.nodeclasses = leginondata.NodeClassesData(nodeclasses=nodeclassnames)
		self.publish(self.nodeclasses, pubevent=True)

	def onNodeOrder(self, evt):
		self.order = list(evt['order']) # make new copy of the list
		self.panel.setOrder(evt['order'])

	def getNodeOrder(self, nodename):
		try:
			return self.order.index(nodename)
		except:
			return 0

	def onCreateNode(self, ievent):
		targetclass = ievent['targetclass']
		try:
			nodeclass = noderegistry.getNodeClass(targetclass)
		except noderegistry.NotFoundError:
			self.confirmEvent(ievent, status='failed')
			return

		nodename = ievent['node']
		session = ievent['session']
		managerlocation = ievent['manager location']

		kwargs = {}
		kwargs['launcher'] = self
		kwargs['otherdatabinder'] = self.databinder
		kwargs['order'] = self.getNodeOrder(nodename)

		if nodeclass.panelclass is not None:
			evt = leginon.gui.wx.Launcher.CreateNodePanelEvent(nodeclass, nodename)
			self.panel.GetEventHandler().AddPendingEvent(evt)
			evt.event.wait()
			kwargs['panel'] = evt.panel

		n = nodeclass(nodename, session, managerlocation, **kwargs)
		self.nodes.append(n)

		evt = leginon.gui.wx.Launcher.CreateNodeEvent(n)
		self.panel.GetEventHandler().AddPendingEvent(evt)

		self.confirmEvent(ievent)

	def onDestroyNode(self, n):
		evt = leginon.gui.wx.Launcher.DestroyNodeEvent(n)
		try:
			self.panel.GetEventHandler().AddPendingEvent(evt)
		except PyDeadObjectError:
			pass

		try:
			self.nodes.remove(n)
		except ValueError:
			pass # ???

def getPrimaryPort(hostname):
	r = leginondata.ClientPortData(hostname=hostname).query()
	if not r:
		return 55555
	else:
		return r[0]['primary port']

if __name__ == '__main__':
	from pyami import mysocket
	import sys

	hostname = mysocket.gethostname().lower()
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
			port  = getPrimaryPort(launchername)
			args, kwargs = (launchername,), {'tcpport': port}
		except:
			args, kwargs = (launchername,), {}
	l = leginon.gui.wx.Launcher.App(*args, **kwargs)
	print kwargs
	l.MainLoop()
	leginondata.sinedon.data.datamanager.exit()

