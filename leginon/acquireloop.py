#!/usr/bin/env python

import timedloop
import time

class AcquireLoop(timedloop.TimedLoop):
	"""
	A node that implements a timed image acquisition loop.
	The default interval is 0 seconds, meaning it will acquire
	images as fast as possible.
	Event Inputs:
		StartEvent - starts the acquisition loop
		StopEvent - stops the acquisition loop
		NumericControlEvent - modifies the loop interval
	"""
	def __init__(self, nodeid, managerlocation):
		timedloop.TimedLoop.__init__(self, nodeid, managerlocation)

	def action(self):
		"""
		this is the real guts of this node
		"""
		## acquire image
		print 'acquiring image %s' % time.asctime()

		## publish image

