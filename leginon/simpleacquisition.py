#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage
import camerafuncs

class SimpleAcquisition(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)

		self.cam = camerafuncs.CameraFuncs(self)

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 400
		self.cam.config(currentconfig)

		self.defineUserInterface()
		self.start()

	def acquireImage(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']

		print 'acquiring image'
		acqtype = self.acqtype.get()
		if acqtype == 'raw': imagedata = self.cam.acquireCameraImageData(camstate,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(camstate,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return
		print 'publishing image'
		self.publish(imagedata, event.CameraImagePublishEvent)
		print 'image published'

		## for xmlrpc
		return ''

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)

		camspec = self.cam.configUIData()

		prefs = self.registerUIContainer('Preferences', (self.acqtype,camspec))

		acq = self.registerUIMethod(self.acquireImage, 'Acquire', ())

		self.registerUISpec('Navigator', (acq, prefs, nodeui))

