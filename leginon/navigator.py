#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage
import camerafuncs
import calibrationclient
import copy
import uidata

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
		movetype = self.movetype.getSelectedValue()
		calclient = self.calclients[movetype]
		newstate = calclient.transform(pixelshift, clickscope, clickcamera)
		emdat = data.ScopeEMData(id=('scope',), initializer=newstate)
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()

		## just in case this is a fake click event
		## (which it is now when it comes from navigator's own image
		if isinstance(clickevent, event.ImageClickEvent):
			self.confirmEvent(clickevent)

	def handleImageAcquire(self, acqevent):
		self.acquireImage()
		self.confirmEvent(acqevent)

	# I wouldn't expect this to actually work
	def handleImageClick2(self, xy):
		click = {'array row': xy[1],
							'array column': xy[0],
							'array shape': self.shape,
							'scope': self.scope,
							'camera': self.camera}
		self.handleImageClick(click)

	def acquireImage(self):
		camconfig = self.cam.cameraConfig()

		print 'acquiring image'
		imagedata = self.cam.acquireCameraImageData(camconfig)

		if imagedata is None:
			return

		self.scope = imagedata['scope']
		self.camera = imagedata['camera']
		self.shape = imagedata['image'].shape
		self.image.setImage(imagedata['image'])

		#print 'publishing image'
		#self.publish(imagedata, pubevent=True)
		#print 'image published'

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		movetypes = self.calclients.keys()
		self.movetype = uidata.UISingleSelectFromList('TEM Parameter', movetypes, 0)
		self.delaydata = uidata.UIFloat('Delay (sec)', 2.5, 'rw')

		cameraconfigure = self.cam.configUIData()

		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((self.movetype, self.delaydata, cameraconfigure))

		acqmeth = uidata.UIMethod('Acquire', self.acquireImage)
		self.image = uidata.UIClickImage('Navigation', self.handleImageClick2, None)
		controlcontainer = uidata.UIContainer('Control')
		controlcontainer.addUIObjects((acqmeth, self.image))

		container = uidata.UIMediumContainer('Navigator')
		container.addUIObjects((settingscontainer, controlcontainer))
		self.uiserver.addUIObject(container)

class SimpleNavigator(Navigator):
	def __init__(self, id, session, nodelocations, **kwargs):
		Navigator.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
