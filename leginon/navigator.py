#!/usr/bin/env python

import node
import event
import data

class Navigator(node.Node):
	def __init__(self, id, nodelocations, emnode=('manager','em')):
		node.Node.__init__(self, id, nodelocations)
		self.emnode = emnode

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventInput(event.ImageAcquireEvent, self.handleImageAcquire)
		self.addEventOutput(event.ImagePublishEvent)

	def handleImageClick(self, clickevent):
		clickinfo = clickevent.content
		## get relavent info from click event
		clickrow = clickinfo['array row']
		clickcol = clickinfo['array column']
		clickshape = clickinfo['array shape']

		## calculate delta from image center
		deltarow = clickrow - clickshape[0] / 2
		deltacol = clickcol - clickshape[1] / 2
		deltarowcol = (deltarow,deltacol)
		print 'deltarowcol', deltarowcol

		## move scope parameter
		self.move(deltarowcol)

		## acquire image
		self.acquireImage()

	def handleImageAcquire(self, acqevent):
		self.acquireImage()

	def move(self, deltarowcol):
		'''deltarowcol is shift in rows and columns'''
		raise NotImplementedError()

	def acquireImage(self):
		print 'acquiring image'
		image = self.researchByDataID('image data')
		image = image.content['image data']
		imagedata = data.ImageData(self.ID(), image)
		print 'publishing image'
		self.publish(imagedata, event.ImagePublishEvent)
		print 'image published'


class StageNavigator(Navigator):
	def __init__(self, id, nodelocations, emnode=('manager','em')): 
		Navigator.__init__(self, id, nodelocations, emnode)

	def move(self, deltarowcol):
		deltax,deltay = self.image2stage(deltarowcol)

		print 'deltaxy', deltax, deltay
		stagepos = self.researchByDataID('stage position').content
		print 'stagepos', stagepos
		curx = stagepos['stage position']['x']
		cury = stagepos['stage position']['y']
		print 'xy', curx, cury
		newx = curx + deltax
		newy = cury + deltay
		print 'newxy', newx, newy

		state = {'stage position': {'x':newx, 'y':newy}}
		print 'state', state
		emdata = data.EMData(self.ID(), state)
		print 'emdata', emdata
		self.publishRemote(self.emnode, emdata)

	def image2stage(self, deltarowcol):
		### this is fake for now, without using calibration
		rows = deltarowcol[0]
		cols = deltarowcol[1]
		stagex = 8e-9 * rows
		stagey = 8e-9 * cols
		return (stagex, stagey)

class ImageShiftNavigator(Navigator):
	def __init__(self, id, nodelocations, emnode=('manager','em')): 
		Navigator.__init__(self, id, nodelocations, emnode)

	def move(self, deltarowcol):
		deltax,deltay = self.image2imageshift(deltarowcol)

		print 'deltaxy', deltax, deltay
		imageshift = self.researchByDataID('image shift').content
		print 'image shift', imageshift
		curx = imageshift['image shift']['x']
		cury = imageshift['image shift']['y']
		print 'xy', curx, cury
		newx = curx + deltax
		newy = cury + deltay
		print 'newxy', newx, newy

		state = {'image shift': {'x':newx, 'y':newy}}
		print 'state', state
		emdata = data.EMData(self.ID(), state)
		print 'emdata', emdata
		self.publishRemote(self.emnode, emdata)

	def image2imageshift(self, deltarowcol):
		### this is fake for now, without using calibration
		rows = deltarowcol[0]
		cols = deltarowcol[1]
		isx = 8e-9 * rows
		isy = 8e-9 * cols
		return (isx, isy)


if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
