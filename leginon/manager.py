#!/usr/bin/env python

import leginonobject
import node
import nodelib
import event
import signal


class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, 'manager', managerloc=None)

		self.nodelib = nodelib

		## this makes every received event get distributed
		self.addEventIn(event.Event, self.eventhandler.distribute)
		self.addEventIn(event.NodeReadyEvent, self.registerNode)
		#self.addDistmap(event.PublishEvent, , ):

		self.main()

	def main(self):
		print self.location()
		self.interact()

	def addDistmap(self, eventclass, from_node=None, to_node=None):
		self.eventhandler.addDistmap(eventclass, from_node, to_node)

	def registerNode(self, readyevent):
		newid = readyevent.origin['id']
		loc = readyevent.origin['location']
		hostname = loc['hostname']
		eventport = loc['event port']
		print 'registering node', newid, hostname, eventport
		self.addEventClient(newid, hostname, eventport)
		print self.eventhandler.clients

	def launch(self, launcher, nodeid, nodeclass, newproc=0):
		"""
		launcher is id of launcher node
		nodeid is the id to assign to the new node
		nodeclass is the class of node to create
		     nodeclass should be accessed thorugh self.nodelib...
		"""
		print 'launch with %s, %s, %s' % (launcher,nodeid,nodeclass)
		ev = event.LaunchEvent(nodeid, nodeclass, newproc)
		print 'pushing LaunchEvent', ev
		self.eventhandler.push(launcher, ev)
		print 'pushed'

if __name__ == '__main__':
	import signal, sys
	m = Manager()
