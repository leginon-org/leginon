#!/usr/bin/env python

import node, event
import time
import data

class GetData(node.Node):
	def __init__(self, id, managerlocation):
		node.Node.__init__(self, id, managerlocation)

		print self.location()
		print self.id

		self.addEventInput(event.PublishEvent, self.handlepublished)

		self.start()

	def handlepublished(self, ievent):
		print "got", self.researchByDataID(ievent.content).content

	def main(self):
		pass

if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['TCP port'] = int(sys.argv[2])

	m = IntGen(manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
