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

		## default camera config
		currentconfig = self.cam.cameraConfig()
		currentconfig['dimension']['x'] = 1024
		currentconfig['binning']['x'] = 4
		currentconfig['exposure time'] = 400
		self.cam.cameraConfig(currentconfig)

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
		movetype = self.movetype.getSelectedValue()[0]
		calclient = self.calclients[movetype]
		newstate = calclient.transform(pixelshift, clickscope, clickcamera)
		emdat = data.ScopeEMData(('scope',), initializer=newstate)
		self.publishRemote(emdat)

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()

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
		camstate = camconfig

		print 'acquiring image'
		acqtype = self.acqtype.getSelectedValue()[0]
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

		self.scope = imagedata['scope']
		self.camera = imagedata['camera']
		self.shape = imagedata['image'].shape
		self.image.setImage(imagedata['image'])

		print 'publishing image'
		self.publish(imagedata, pubevent=True)
		print 'image published'

	def defineUserInterface(self):
		node.Node.defineUserInterface(self)
		movetypes = self.calclients.keys()
		if movetypes:
			selected = [0]
		else:
			selected = []
		self.movetype = uidata.UISelectFromList('TEM Parameter', movetypes,
																						selected, 'r')
		self.delaydata = uidata.UIFloat('Delay (sec)', 2.5, 'rw')

		self.acqtype = uidata.UISelectFromList('Acquisition Type',
																						('raw', 'corrected'), [0], 'r')
		cameraconfigure = self.cam.configUIData()

		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((self.movetype, self.delaydata, self.acqtype, cameraconfigure))

		self.image = uidata.UIClickImage('Navigation', self.handleImageClick2, None)
		controlcontainer = uidata.UIContainer('Control')
		controlcontainer.addUIObject(self.image)

		container = uidata.UIMediumContainer('Navigator')
		container.addUIObjects((settingscontainer, controlcontainer))
		self.uiserver.addUIObject(container)

#		nodeui = node.Node.defineUserInterface(self)
#
#		movetypes = self.calclients.keys()
#		temparam = self.registerUIData('temparam', 'array', default=movetypes)
#		self.movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw', default='image shift')
#
#		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')
#
#		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
#		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)
#
#		prefs = self.registerUIContainer('Preferences', (self.movetype, self.delaydata, self.acqtype))
#
#		camspec = self.cam.configUIData()
#
#		myui = self.registerUISpec('Navigator', (prefs, camspec))
#		myui += nodeui
#		return myui

class SimpleNavigator(Navigator):
	def __init__(self, id, session, nodelocations, **kwargs):
		Navigator.__init__(self, id, session, nodelocations, **kwargs)
		self.defineUserInterface()
		self.start()


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
