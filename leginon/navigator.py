#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage
import camerafuncs
import calibrationclient
import copy

class Navigator(node.Node):
	def __init__(self, id, session, nodelocations, **kwargs):
		node.Node.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.calclients = {
			'image shift': calibrationclient.ImageShiftCalibrationClient(self),
			'beam shift': calibrationclient.BeamShiftCalibrationClient(self),
			'stage position': calibrationclient.StageCalibrationClient(self),
			'modeled stage position': calibrationclient.ModeledStageCalibrationClient(self)
		}

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.ImageAcquireEvent, self.handleImageAcquire)
		self.addEventOutput(event.CameraImagePublishEvent)

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 400
		self.cam.config(currentconfig)

	def handleImageClick(self, clickevent):
		print 'handling image click'
		clickinfo = copy.deepcopy(clickevent)
		## get relavent info from click event
		clickrow = clickinfo['array row']
		clickcol = clickinfo['array column']
		clickshape = clickinfo['array shape']
		clickscope = clickinfo['scope']
		clickcamera = clickinfo['camera']

		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		## to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		pixelshift = {'row':deltarow, 'col':deltacol}
		mag = clickscope['magnification']

		## figure out shift
		movetype = self.movetype.get()
		calclient = self.calclients[movetype]
		newstate = calclient.transform(pixelshift, clickscope, clickcamera)
		emdat = data.EMData(('scope',), em=newstate)
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()

	def acquireImage(self):
		camconfig = self.cam.config()
		camstate = camconfig['state']

		print 'acquiring image'
		acqtype = self.acqtype.get()
		if acqtype == 'raw':
			imagedata = self.cam.acquireCameraImageData(camstate,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(camstate,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return
		print 'publishing image'
		self.publish(imagedata, pubevent=True)
		print 'image published'

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		movetypes = self.calclients.keys()
		temparam = self.registerUIData('temparam', 'array', default=movetypes)
		self.movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw', default='image shift')

		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)

		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype))

		camspec = self.cam.configUIData()

		myui = self.registerUISpec('Navigator', (prefs, camspec))
		myui += nodeui
		return myui

class SimpleNavigator(Navigator):
	def __init__(self, id, session, nodelocations, **kwargs):
		Navigator.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
