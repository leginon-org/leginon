#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import array, base64
import watcher
import event, data
import copy

class ImageWatcher(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.ImagePublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.ImageProcessDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = [event.ImagePublishEvent]
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, **kwargs)

		self.iv = None
		self.numarray = None
		self.currentimagedata = None

	def processData(self, somedata):
		if not isinstance(somedata, data.ImageData):
			raise RuntimeError('Data is not ImageData instance')
		self.currentimagedata = somedata
		self.numarray = somedata['image']
		self.processImageData(somedata)
		self.sendImageProcessDone()

	def sendImageProcessDone(self, status='ok'):
		imageid = self.currentimagedata['id']
		ev = event.ImageProcessDoneEvent(id=self.ID(), imageid=imageid, status=status)
		print '%s sending %s' % (self.id, ev)
		self.outputEvent(ev)

	def processImageData(self, imagedata):
		raise NotImplementedError('implement processImageData in subclasses of ImageWatcher')
