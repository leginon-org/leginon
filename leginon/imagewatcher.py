#!/usr/bin/env python

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
		self.imagedata = None

	def imageInfo(self):
		'''
		add some info to clickinfo to create targetinfo
		'''
		imageinfo = {}
		imageinfo['scope'] = self.imagedata['scope']
		imageinfo['camera'] = self.imagedata['camera']
		if 'preset' in self.imagedata and self.imagedata['preset'] is not None:
			imageinfo['preset'] = self.imagedata['preset']
		imageinfo['source'] = 'click'
		return copy.deepcopy(imageinfo)

	def processData(self, somedata):
		if not isinstance(somedata, data.ImageData):
			raise RuntimeError('Data is not ImageData instance')
		self.imagedata = somedata
		self.numarray = somedata['image']
		self.processImageData(somedata)
		self.sendImageProcessDone()

	def sendImageProcessDone(self, status='ok'):
		imageid = self.imagedata['id']
		ev = event.ImageProcessDoneEvent(id=self.ID(), imageid=imageid, status=status)
		print '%s sending %s' % (self.id, ev)
		self.outputEvent(ev)

	def processImageData(self, imagedata):
		raise NotImplementedError('implement processImageData in subclasses of ImageWatcher')
