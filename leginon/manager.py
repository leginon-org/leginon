#!/usr/bin/env python

import leginonobject
import node
import event
import signal


class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, managerloc=None)

		## this makes every received event get distributed
		self.addEventIn(event.Event, self.eventhandler.distribute)
		self.addEventIn(event.NodeReadyEvent, self.registerNode)
		#self.addDistmap(event.PublishEvent, , ):

		self.main()

	def main(self):
		print self.location()
		while 1:
			try:
				input('command> ')
			except KeyboardInterrupt:
				sys.exit()
			except:
				print 'ERROR'

	def addDistmap(self, eventclass, from_node=None, to_node=None):
		self.eventhandler.addDistmap(eventclass, from_node, to_node)

	def registerNode(self, readyevent):
		id = readyevent.origin['id']
		loc = readyevent.origin['location']
		hostname = loc['hostname']
		eventport = loc['event port']
		print 'registering node', id, hostname, eventport
		self.addEventClient(id, hostname, eventport)

if __name__ == '__main__':
	import signal, sys
	m = Manager()

	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
