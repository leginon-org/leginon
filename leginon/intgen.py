#!/usr/bin/env python

import node, event
import time
import data

class IntGen(node.Node):
	def __init__(self, managerlocation):
		node.Node.__init__(self, managerlocation)

		#self.addEventOut(event.ControlEvent)
		self.addEventOut(event.PublishEvent)

		print self.location()
		print self.id
		self.main()
			
	def main(self):
		while 1:
			stuff = raw_input('enter integer> ')
			print 'stuff %s' % stuff
			try:
				stuff = data.IntData(stuff)
				print 'stuff after int %s' % stuff
			except ValueError:
				print 'you did not enter an integer'
				continue

			#ev = event.ControlEvent(param=stuff)
			self.publish(stuff, event.PublishEvent)


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
