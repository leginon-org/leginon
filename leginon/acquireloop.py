#!/usr/bin/env python

import timedloop
import time
#import Numeric
import base64
import array

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

		# this is rough, ImageData type, etc. to come soon
		imagedata = self.researchByDataID('image data')
		image = base64.decodestring(imagedata.content['image data'])

		imagedatatype = self.researchByDataID('datatype code')
		datatype = imagedatatype.content['datatype code']

		imagearray = array.array(datatype, image)
		print 'image 1...10', imagearray[:10]

		#imagedata = self.researchByDataID('image data')
		#print 'image 1...10', imagedata.content['image data'][:10]

		## acquire image
		print 'acquiring image %s' % time.asctime()

		## publish image

