#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import leginondata
import event
import watcher

class ImageWatcher(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.ImagePublishEvent,
																								event.ImageListPublishEvent,
																								event.QueuePublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.ImageProcessDoneEvent]
	def __init__(self, id, session, managerlocation, **kwargs):
		watchfor = [event.ImagePublishEvent, event.ImageListPublishEvent, event.QueuePublishEvent]
		watcher.Watcher.__init__(self, id, session, managerlocation, watchfor,
															**kwargs)

		self.numarray = None
		self.currentimagedata = None

	def processImageData(self, imagedata):
		raise NotImplementedError

	def publishImageProcessDone(self, imageid=None, status='ok'):
		if imageid is None:
			imageid = self.currentimagedata.dbid
		initializer = {'imageid': imageid, 'status': status}
		oevent = event.ImageProcessDoneEvent(initializer=initializer)
		self.outputEvent(oevent)

	def processData(self, idata):
		if isinstance(idata, leginondata.ImageData):
			self.setStatus('processing')
			self.logger.debug('Imagewathcer.processData (ImageData)')
			imageid = idata.dbid
			self.currentimagedata = idata

			self.numarray = idata['image']
			self.processImageData(idata)
			self.publishImageProcessDone(imageid)
			self.logger.debug('Imagewathcer.processData (ImageData) done')
			self.setStatus('idle')
		elif isinstance(idata, leginondata.ImageListData):
			self.setStatus('processing')
			self.logger.debug('Imagewathcer.processData (ImageListData)')
			self.processImageListData(idata)
			if 'images' in idata and idata['images'] is not None:
				for ref in idata['images']:
					imageid = ref.dbid
					self.publishImageProcessDone(imageid=imageid)
			self.logger.debug('Imagewathcer.processData (ImageListData) done')
			self.setStatus('idle')
		else:
			self.setStatus('idle')
			raise TypeError('data to be processed must be an ImageData instance')

