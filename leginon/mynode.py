#!/usr/bin/env python

import node, event
import time
import data

class MyNode(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		#self.addEventIn(event.ControlEvent, self.handle_intervalchange)
		self.addEventIn(event.PublishEvent, self.handle_intervalpublished)
		self.addEventOut(event.PublishEvent)

		self.interval = 5
		print self.location()
		print self.nodeid
		self.main()

	def main(self):
		while 1:
			self.print_stuff()
			time.sleep(self.interval)

	def print_stuff(self):
		timenow = time.asctime()
		print timenow
		mydata = data.StringData(timenow)
		self.publish(mydata, event.PublishEvent)

	def handle_intervalchange(self, controlevent):
		print 'got control event %s' % controlevent
		new_interval = controlevent.content
		print 'new_interval %s is type %s' % (new_interval, type(new_interval))
		self.change_interval(new_interval)

	def handle_intervalpublished(self, publishevent):
		dataid = publishevent.content
		print 'publish event %s dataid %s' % (publishevent, dataid)
		datahost = publishevent.origin['location']['hostname']
		dataport = publishevent.origin['location']['data port']
		dataserv = (datahost,dataport)
		new_interval = self.research(dataserv, dataid)
		print 'new_interval %s is type %s' % (new_interval, type(new_interval))
		self.change_interval(new_interval.content)

	def change_interval(self, new_interval):
		self.interval = new_interval




if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['event port'] = int(sys.argv[2])

	m = MyNode(None, manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
