#!/usr/bin/env python

import node, event
import time
import data

class IntGen(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		#self.addEventOutput(event.ControlEvent)
		self.addEventOutput(event.PublishEvent)

		print self.location()
		print self.nodeid
		self.main()

	def sendint(self, newint):
		intdata = data.IntData(newint)
		self.publish(intdata, event.PublishEvent)
		
			
	def main(self):
		self.interact()


if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['event port'] = int(sys.argv[2])

	m = IntGen(manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
