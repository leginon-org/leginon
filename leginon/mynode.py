#!/usr/bin/env python

import node, event
import time
import data

class MyNode(node.Node):
	def __init__(self, id, managerlocation):
		node.Node.__init__(self, id, managerlocation)

		self.addEventInput(event.NumericControlEvent, self.handle_intervalchange)
		self.addEventInput(event.StartEvent, self.main)
		self.addEventInput(event.PublishEvent, self.handle_intervalpublished)

		self.interval = 5
		print self.location()
		self.main()

	def main(self, startevent=None):
		#for i in [1,2,3]:
		while 1:
			self.print_stuff()
			time.sleep(self.interval)
		#self.unregister()

	def unregister(self):
		self.announce(event.NodeUnavailableEvent(self.ID()))

	def print_stuff(self):
		self.timenow = time.asctime()
		print 'node %s says %s' % (self.id,self.timenow)
		mydata = data.StringData(self.ID(), self.timenow)
		self.publish(mydata)

	def handle_intervalchange(self, controlevent):
		print 'got control event %s' % controlevent
		new_interval = controlevent.content
		print 'new_interval %s is type %s' % (new_interval, type(new_interval))
		self.change_interval(new_interval)

	def handle_intervalpublished(self, publishevent):
		dataid = publishevent.content
		print 'publish event %s dataid %s' % (publishevent, dataid)
		new_interval = self.research(publishevent.content, dataid)
		print 'new_interval %s is type %s' % (new_interval, type(new_interval))
		self.change_interval(new_interval.content)

	def change_interval(self, new_interval):
		self.interval = new_interval




if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['TCP port'] = int(sys.argv[2])

	m = MyNode(None, manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
