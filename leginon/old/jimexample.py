#!/usr/bin/env python

import nodenet
import event

class Node1(nodenet.Node):
	def __init__(self, manageraddress):
		nodenet.Node.__init__(self, 'Node1', manageraddress)

		data1 = {'x':111, 'y':222}
		self.publish('data1', data1)

		data2 = range(4000000)
		self.publish('data2', data2)

class Node2(nodenet.Node):
	def __init__(self, manageraddress):
		nodenet.Node.__init__(self, 'Node2', manageraddress)
	
	def EXPORT_getdata1(self):
		data = self.research('data1')
		print 'Node2 got this from Node1:', data

	def EXPORT_getdata2(self):
		data = self.research('data2')
		print 'Node2 got this from Node1:', len(data), data[200]

	def EXPORT_announce(self):
		e = nodenet.Event()
		self.announce(e)


class MyNode(nodenet.Node):

	def __init__(self, manageraddress = None):

		self.eventmap = {
			event.MyEvent:  self.handleMyEvent,
			event.YourEvent:  self.handleYourEvent
			}

		nodenet.Node.__init__(self, 'Node3', manageraddress)

	def handleMyEvent(self, ev):
		print 'handleMyEvent got the event: ', ev

	def handleYourEvent(self, ev):
		print 'handleYourEvent got the event: ', ev


if __name__ == '__main__':
	import sys, signal

	myclass = sys.argv[1]

	if myclass == 'Manager':
		mynode = nodenet.Manager()
		print '%s running on port %s' % (myclass, mynode.port)
	elif myclass == 'Node1':
		manageraddress = (sys.argv[2], int(sys.argv[3]))
		mynode = Node1(manageraddress)
		print '%s running on port %s' % (myclass, mynode.port)
		print 'dataport', mynode.dataport
	elif myclass == 'Node2':
		manageraddress = (sys.argv[2], int(sys.argv[3]))
		mynode = Node2(manageraddress)
		print '%s running on port %s' % (myclass, mynode.port)
		print 'dataport', mynode.dataport

	try:
		signal.pause()
	except:
		del(mynode)
		sys.exit(0)
