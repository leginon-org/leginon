#!/usr/bin/env python

import timedloop
import event
import data
import time
#import Numeric
import threading

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
	def __init__(self, id, nodelocations):
		timedloop.TimedLoop.__init__(self, id, nodelocations)
		print 'AcquireLoop started', self.id

	def action(self):
		"""
		this is the real guts of this node
		"""

		# this is rough, ImageData type, etc. to come soon
		camerastate = self.researchByDataID('camera')
		t = threading.Thread(name='process image thread', target=self.process, args=(camerastate,))
		t.setDaemon(1)
		t.start()

	def process(self, camerastate):
		## publish image
		imagedata = data.ImageData(self.ID(), camerastate.content['image data'])
		self.publish(imagedata, event.ImagePublishEvent)

		imagearray = camerastate.content['image data']
		print 'image 1...10', imagearray[:10,:10]

		del camerastate.content['image data']
		print camerastate.content

		## acquire image
		print 'acquiring image %s' % time.asctime()


