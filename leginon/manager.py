#!/usr/bin/env python

import leginonobject
import node
import common
import event
import signal

import os

class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, 'manager', managerloc=None)

		self.common = common

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

	def launchNode(self, launcher, newproc, target, newid):
		manloc = self.location()
		args = (newid, manloc)
		self.launch(launcher, newproc, target, args)

	def launchServer(self, launcher, newproc, target):
		self.launch(launcher, newproc, target)

	def launch(self, launcher, newproc, target, args=(), kwargs={}):
		"""
		launcher = id of launcher node
		newproc = flag to indicate new process, else new thread
		target = callable object under self.common
		args, kwargs = args for callable object
		"""
		#ev = event.LaunchEvent(nodeid, nodeclass, newproc)
		ev = event.LaunchEvent(newproc, target, args, kwargs)
		self.eventhandler.push(launcher, ev)

if __name__ == '__main__':
	import signal, sys
	m = Manager()
