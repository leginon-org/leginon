#!/usr/bin/env python

import array, base64

import ImageViewer

import watcher
import event, data


###
### this is very unorganized,  need to separate the ImageViewer stuff into
### another class or into ImageViewer itself
###

class ImageWatcher(watcher.Watcher):
	def __init__(self, id, nodelocations, **kwargs):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking, **kwargs)
		self.addEventOutput(event.ImageClickEvent)

		self.iv = None
		self.numarray = None
		self.imagedata = None
		#self.start_viewer_thread()

		self.clickactions = ('ImageClickEvent', 'Target Editor')

	def imageInfo(self):
		'''
		add some info to clickinfo to create targetinfo
		'''
		imageinfo = {}
		imageinfo['image id'] = self.imagedata.id
		imageinfo['scope'] = self.imagedata.content['scope']
		imageinfo['camera'] = self.imagedata.content['camera']
		if 'preset' in self.imagedata.content:
			imageinfo['preset'] = self.imagedata.content['preset']
		imageinfo['source'] = 'click'
		return imageinfo

	def processData(self, imagedata):
		if not isinstance(imagedata, data.ImageData):
			raise RuntimeError('Data is not ImageData instance')
		self.imagedata = imagedata
		self.numarray = imagedata.content['image']

	def OLDselectClickAction(self, value=None):
		if value is not None:
			self.clickaction = value

		## turn off callbacks
		self.iv.canvas.targetClickerOff()
		self.clickEventOff()

		## choose new callback to turn on
		if self.clickaction == 'ImageClickEvent':
			self.clickEventOn()
		elif self.clickaction == 'Target Editor':
			self.iv.canvas.targetClickerOn()
			
		return self.clickaction

	def defineUserInterface(self):
		return watcher.Watcher.defineUserInterface(self)

