#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage

class Navigator(node.Node):
	def __init__(self, id, nodelocations):
		self.shift_types = {
			'image shift': event.ImageShiftPixelShiftEvent,
			'stage': event.StagePixelShiftEvent,
			'no preference': event.PixelShiftEvent
		}

		## by default, use the generic PixelShiftEvent
		self.shiftType('image shift')

		node.Node.__init__(self, id, nodelocations)

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.ImageAcquireEvent, self.handleImageAcquire)
		self.addEventOutput(event.ImagePublishEvent)
		self.addEventOutput(event.PixelShiftEvent)

	def die(self, killevent):
		self.exit()

	def shiftType(self, shift_type=None):
		'''
		this sets the event to be generated for a move
		it must be a subclass of PixelShiftEvent
		'''
		if shift_type is None:
			return self.current_shift_type
		
		if shift_type not in self.shift_types:
			raise RuntimeError('no such shift type: %s' % shift_type)
		self.current_shift_type = shift_type
		self.shiftEventClass = self.shift_types[shift_type]

	def handleImageClick(self, clickevent):
		print 'handling image click'
		clickinfo = clickevent.content
		## get relavent info from click event
		clickrow = clickinfo['array row']
		clickcol = clickinfo['array column']
		clickshape = clickinfo['array shape']

		print 'clickinfo', clickinfo
		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2

		## to shift clicked point to center...
		deltarow = -deltarow
		deltacol = -deltacol

		deltarowcol = {'row':deltarow, 'column':deltacol}
		print 'deltarowcol', deltarowcol

		## do pixel shift
		e = self.shiftEventClass(self.ID(), deltarowcol)
		print 'e', e
		self.outputEvent(e)
		print 'outputEvent done'

		# wait for a while
		time.sleep(self.delaydata.get())

		## acquire image
		self.acquireImage()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()

	def acquireImage(self):
		print 'setting camera state'
		camstate = self.camdata.get()
		camdata = data.EMData('camera', camstate)
		print 'publishing camera state'
		self.publishRemote(camdata)

		print 'acquiring image'
		acqtype = self.acqtype.get()
		if acqtype == 'raw':
			print 'acquiring raw image'
			image = self.researchByDataID('image data')
			image = image.content['image data']
		elif acqtype == 'corrected':
			print 'acquiring corrected image'
			image = self.researchByDataID('normalized image data')
			image = image.content

		imagedata = data.ImageData(self.ID(), image)
		print 'publishing image'
		self.publish(imagedata, event.ImagePublishEvent)
		print 'image published'

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		shift_types = self.shift_types.keys()
		temparam = self.registerUIData('temparam', 'array', default=shift_types)
		movetype = self.registerUIData('TEM Parameter', 'string', choices=temparam, permissions='rw')
		movetype.set(self.shiftType)

		self.delaydata = self.registerUIData('Delay (sec)', 'float', default=2.5, permissions='rw')

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)

		prefs = self.registerUIContainer('Preferences', (movetype, self.delaydata, self.acqtype))

		### Camera State Data Spec
		defaultsize = (512,512)
		camerasize = (2048,2048)
		offset = cameraimage.centerOffset(camerasize,defaultsize)
		camstate = {
			'exposure time': 500,
			'binning': {'x':1, 'y':1},
			'dimension': {'x':defaultsize[0], 'y':defaultsize[1]},
			'offset': {'x': offset[0], 'y': offset[1]}
		}
		self.defaultcamstate = camstate
		self.camdata = self.registerUIData('Camera', 'struct', default=camstate)

		self.registerUISpec('Navigator', (prefs, self.camdata, nodeui))


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
