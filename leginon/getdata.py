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
		print "GetData researching id", ievent.content
		idata = self.researchByDataID(ievent.content).content
		print "received idata =", idata
		self.confirmEvent(ievent)

	def main(self):
		pass

if __name__ == '__main__':
	pass
