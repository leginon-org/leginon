#!/usr/bin/env python

import leginonobject
import node
import event
import signal

class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, managerloc=None)

		nodebindings = NodeBindings()
		self.nodes = {}

		self.eventhandler.bind(event.Event, self.distribute)

	def main(self):
		signal.pause()

	def distribute(self, event):
		'''distribute event to any location in the nodebindings'''
		pass
		print 'got event %s' % event
		

	def publish(self, data):
		self.datahandler.insert(data)

	def research(self, dataid):
		return self.datahandler.pull(dataid)

	def addEventClient(self, host, port):
		self.nodes[(host,port)] = self.eventhandler.addClient(host, port)


class NodeBindings(dict, leginonobject.LeginonObject):
	def __init__(self, *args):
		dict.__init__(self, *args)
		leginonobject.LeginonObject.__init__(self)

if __name__ == '__main__':
	import signal, sys
	m = Manager()
	loc = m.location()
	print 'location:  %s' % loc

	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
