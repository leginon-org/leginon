#!/usr/bin/env python

import nodenet
import event


class Node1(nodenet.Node):

	def __init__(self, manageraddress = None):
		nodenet.Node.__init__(self, manageraddress)
		self.yourcount = self.mycount = 0

	def init_events(self):
		self.events = event.NodeEvents()
		self.events.addInput(event.MyEvent, self.handleMyEvent)
		self.events.addInput(event.YourEvent, self.handleYourEvent)
		self.events.addOutput(event.MyEvent)
		self.events.addOutput(event.YourEvent)

	def handleMyEvent(self, ev):
		print 'handleMyEvent got the event: ', ev

	def handleYourEvent(self, ev):
		print 'handleYourEvent got the event: ', ev

	def EXPORT_myevent(self):
		self.mycount += 1
		print 'announcing MyEvent'
		self.announce(event.MyEvent(self.mycount))
		return ''

	def EXPORT_yourevent(self):
		self.yourcount += 1
		print 'announcing YourEvent'
		self.announce(event.YourEvent(self.yourcount))
		return ''



if __name__ == '__main__':
	import sys, signal

	host = sys.argv[1]
	port = int(sys.argv[2])

	manaddress = (host,port)

	n1 = Node1(manaddress)

	try:
		signal.pause()
	except:
		del(n1)
		sys.exit(0)
