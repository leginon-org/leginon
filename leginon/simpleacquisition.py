#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage
import camerafuncs
import presets

class SimpleAcquisition(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)

		self.cam = camerafuncs.CameraFuncs(self)
		self.presetsclient = presets.PresetsClient(self)

		## default camera config

		self.defineUserInterface()
		self.start()

	def acquireImage(self):
		presetname = self.presetname.get()
		print 'going to preset %s' % (presetname,)
		preset = self.presetsclient.getPreset(presetname)
		print 'preset mag:', preset['magnification']
		self.presetsclient.toScope(preset)
		time.sleep(2)

		print 'acquiring image'
		acqtype = self.acqtype.get()
		if acqtype == 'raw': imagedata = self.cam.acquireCameraImageData(None,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(camstate,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return
		## attach preset to imagedata
		imagedata.content['preset'] = dict(preset)

		print 'publishing image'
		self.publish(imagedata, event.CameraImagePublishEvent)
		print 'image published'

		## for xmlrpc
		return ''

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)

		self.presetname = self.registerUIData('Preset Name', 'string', default='p56', permissions='rw')

		prefs = self.registerUIContainer('Preferences', (self.acqtype,self.presetname))

		acq = self.registerUIMethod(self.acquireImage, 'Acquire', ())

		self.registerUISpec('Navigator', (acq, prefs, nodeui))

