#!/usr/bin/env python

import nodenet
import event

class Node2(nodenet.Node):

	def __init__(self, manageraddress = None):
		nodenet.Node.__init__(self, manageraddress)

	def __del__(self):
		print 'Node2.__del__, calling Node.__del__'
		nodenet.Node.__del__(self)
		print 'Node2.__del__, done calling Node.__del__'

	def init_events(self):
		self.events.addInput(event.YourEvent, self.handleYourEvent)
		self.events.addInput(event.MyEvent, self.handleMyEvent)
		self.events.addOutput(event.MyEvent)

	def handleMyEvent(self, ev):
		print 'Node2.handleMyEvent got the event: ', ev

	def handleYourEvent(self, ev):
		print 'Node2.handleYourEvent got the event: ', ev

	def EXPORT_myevent(self):
		print 'announcing MyEvent'
		self.announce(event.MyEvent(555))
		return ''


if __name__ == '__main__':
	import sys, signal

	host = sys.argv[1]
	port = int(sys.argv[2])

	manaddress = (host,port)

	n2 = Node2(manaddress)

	try:
		signal.pause()
	except:
		n2.unregister()
		print "DONE"
		sys.exit(0)
