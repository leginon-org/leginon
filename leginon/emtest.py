#!/usr/bin/env python

import node, event
import time
import data

class EMTest(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		#self.addEventInput(event.ControlEvent, self.handle_intervalchange)
		#self.addEventInput(event.PublishEvent, self.handle_intervalpublished)
		#self.addEventOutput(event.PublishEvent)

		print "starting emtest..."
		maglocdata = self.research(self.managerloc, 'magnification')
		magdata = self.research(maglocdata.content[0], 'magnification')
		print magdata.content
		magdata.content['magnification'] = 1000
		self.publishRemote(maglocdata.content[0], magdata)
		newmagdata = self.research(maglocdata.content[0], 'magnification')
		print newmagdata.content

if __name__ == '__main__':
	pass

