#!/usr/bin/env python

import array, base64

import ImageViewer

import watcher
import event, data
import copy


###
### this is very unorganized,  need to separate the ImageViewer stuff into
### another class or into ImageViewer itself
###

class ImageWatcher(watcher.Watcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, lockblocking, **kwargs)

		self.iv = None
		self.numarray = None
		self.imagedata = None

	def imageInfo(self):
		'''
		add some info to clickinfo to create targetinfo
		'''
		imageinfo = {}
#		imageinfo['image id'] = self.imagedata['id']
		imageinfo['scope'] = self.imagedata['scope']
		imageinfo['camera'] = self.imagedata['camera']
		if 'preset' in self.imagedata and self.imagedata['preset'] is not None:
			imageinfo['preset'] = self.imagedata['preset']
		imageinfo['source'] = 'click'
		return copy.deepcopy(imageinfo)

	def processData(self, imagedata):
		if not isinstance(imagedata, data.ImageData):
			raise RuntimeError('Data is not ImageData instance')
		self.imagedata = imagedata
		self.numarray = imagedata['image']
