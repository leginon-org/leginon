#!/usr/bin/env python

import node, event
import time
import data

class MyNode(node.Node):
	def __init__(self, managerlocation):
		node.Node.__init__(self, managerlocation)

		self.addEventIn(ControlEvent, self.handle_intervalchange)
		self.addEventOut(PublishEvent)

		self.interval = 2
		self.main()

	def main(self):
		while 1:
			self.print_stuff()
			time.sleep(self.interval)

	def print_stuff(self):
		timenow = time.asctime()
		print timenow
		mydata = StringData(self, timenow)
		newid = self.publish(mydata)
		myevent = event.PublishEvent(newid)
		self.announce(myevent)

	def handle_intervalchange(self, controlevent):
		new_interval = controlevent.content
		self.change_interval(new_interval)

	def change_interval(self, new_interval):
		self.interval = new_interval


class StringData(data.Data):
	def __init__(self, creator, content):
		if type(content) != str:
			raise TypeError('StringData content must be string')
		data.Data.__init__(self, creator, content)


if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['event port'] = int(sys.argv[2])

	m = MyNode(manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
