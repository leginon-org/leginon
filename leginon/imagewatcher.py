#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
import event
import watcher

class ImageWatcher(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.ImagePublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.ImageProcessDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = [event.ImagePublishEvent]
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor,
															**kwargs)

		self.numarray = None
		self.currentimagedata = None

	def processImageData(self, imagedata):
		raise NotImplementedError

	def publishImageProcessDone(self, status='ok'):
		imageid = self.currentimagedata['id']
		initializer = {'id': self.ID(),
										'imageid': self.currentimagedata['id'],
										'status': status}
		oevent = event.ImageProcessDoneEvent(initializer=initializer)
		self.outputEvent(oevent)

	def processData(self, idata):
		if not isinstance(idata, data.ImageData):
			raise TypeError('data to be processed is not an ImageData instance')
		self.currentimagedata = idata
		self.numarray = idata['image']
		self.processImageData(idata)
		self.publishImageProcessDone()

