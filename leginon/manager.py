#!/usr/bin/env python

import leginonobject
import node
import event
import signal


class Manager(node.Node):
	def __init__(self):
		node.Node.__init__(self, managerloc=None)

		## this makes every received event get distributed
		self.addEventIn(event.Event, self.eventhandler.distribute)
		#self.addDistmap(event.PublishEvent, , ):

		self.main()

	def main(self):
		print self.location()
		while 1:
			try:
				input('command> ')
			except KeyboardInterrupt:
				sys.exit()
			except:
				print 'ERROR'

	def addEventClient(self, host, port):
		self.eventhandler.addClient(host, port)



if __name__ == '__main__':
	import signal, sys
	m = Manager()

	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
