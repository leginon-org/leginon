#!/usr/bin/env python

import leginonobject
import node
import event
import signal

class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, managerloc=None)
		self.nodebindings = NodeBindings()
		self.nodes = {}
		self.addEventIn(event.Event, self.distribute)

	def main(self):
		signal.pause()

					
		
				
	def addEventClient(self, host, port):
		self.nodes[(host,port)] = self.eventhandler.addClient(host, port)



if __name__ == '__main__':
	import signal, sys
	m = Manager()
	loc = m.location()
	print 'location:  %s' % loc

	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
