#!/usr/bin/env python

import node, event
import threading, time
import data

class AcquireLoop(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		self.addEventInput(event.StartEvent, self._handle_start)
		self.addEventInput(event.StopEvent, self._handle_stop)
		self.addEventInput(event.NumericControlEvent, self._handle_intervalchange)

		self.interval = 0
		self.acqevent = threading.Event()
		self.stopevent = threading.Event()
		self.mainlock = threading.RLock()

		self.interact()

	def main(self):
		### main can only be run once
		if not self.mainlock.acquire(blocking=0):
			return

		self.stopevent.clear()
		while 1:
			## check for a stop event
			if self.stopevent.isSet():
				break

			## set a timer for the next acquire
			self.acqevent.clear()
			threading.Timer(self.interval,self._acqtimer).start()

			## this acuqire
			self._acquire()

			## wait until the next acquire
			self.acqevent.wait()

		self.mainlock.release()

	def _acqtimer(self):
		"called to initiate the next acquire"
		self.acqevent.set()

	def _handle_start(self, startevent):
		"""
		start a new main thread
		"""
		t = threading.Thread(target=self.main)
		t.setDaemon(1)
		t.start()

	def _handle_stop(self, stopevent):
		self.stopevent.set()

	def _handle_intervalchange(self, numcontrolevent):
		print 'got control event %s' % numcontrolevent
		new_interval = numcontrolevent.content
		self._change_interval(new_interval)

	def _change_interval(self, new_interval):
		self.interval = new_interval

	def _acquire(self):
		print 'acquiring image %s' % time.asctime()


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
