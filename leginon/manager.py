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
		self.addEventInput(event.Event, self.distribute)
		self.addEventInput(event.NodeReadyEvent, self.registerNode)
		#self.addDistmap(event.PublishEvent, , ):

		self.main()

	def main(self):
		print self.location()
		self.interact()

	# now addEventDistmap inherited from node
#	def addDistmap(self, eventclass, from_node=None, to_node=None):
#		self.eventhandler.addDistmap(eventclass, from_node, to_node)

	def registerNode(self, readyevent):
		newid = readyevent.origin['id']
		loc = readyevent.origin['location']
		hostname = loc['hostname']
		eventport = loc['TCP port']
		print 'registering node', newid, hostname, eventport
		self.addEventClient(newid, hostname, eventport)
		print self.clients

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
		self.clients[launcher].push(ev)

	def addEventDistmap(self, eventclass, from_node=None, to_node=None):
		if eventclass not in self.distmap:
			self.distmap[eventclass] = {}
		if from_node not in self.distmap[eventclass]:
			self.distmap[eventclass][from_node] = []
		if to_node not in self.distmap[eventclass][from_node]:
			self.distmap[eventclass][from_node].append(to_node)

	def distribute(self, ievent):
		'''push event to eventclients based on event class and source'''
		#print 'DIST', event.origin
		eventclass = ievent.__class__
		from_node = ievent.origin['id']
		done = []
		for distclass,fromnodes in self.distmap.items():
			if issubclass(eventclass, distclass):
				for fromnode in (from_node, None):
					if fromnode in fromnodes:
						for to_node in fromnodes[from_node]:
							if to_node:
								if to_node not in done:
									self.clients[to_node].push(ievent)
									done.append(to_node)
							else:
								for to_node in self.handler.clients:
									if to_node not in done:
										self.clients[to_node].push(ievent)
										done.append(to_node)

if __name__ == '__main__':
	import signal, sys
	m = Manager()

