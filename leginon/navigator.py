#!/usr/bin/env python

import node, event

class Navigator(node.Node):
	def __init__(self, id, managerlocation, emnode='em'):
		node.Node.__init__(self, id, managerlocation)
		self.emnode = emnode

		self.addEventInput(event.ImageClickEvent, self.handleImageClick)
		self.addEventOutput(event.ImagePublishEvent)

	def handleImageClick(self, clickevent):
		clickrow = clickevent['array row']
		clickcol = clickevent['array column']
		deltaimage = (clickrow,clickcol)
		print 'deltaimage', deltaimage
		deltastage = self.image2stage(deltaimage)
		print 'deltastage', deltastage
		self.moveAcquire(deltastage)

	def moveAcquire(self, deltaxy):
		self.moveStage(deltaxy)
		self.acquireImage(self)

	def moveStage(self, deltaxy):
		stagepos = self.researchByDataID('stage position')
		curx = stagepos['x']
		cury = stagepos['y']
		newx = curx + delata[0]
		newy = cury + delata[1]
		emdata = data.EMData(self.ID(), state)
		self.publishRemote(self.emnode, emdata)

	def acquireImage(self):
		print 'acquiring image'
		image = self.researchByDataID('image data')
		image = imagedata.content['image data']
		imagedata = data.ImageData(self.ID(), image)
		self.publish(imagedata, event.ImagePublishEvent)

	def image2stage(self, imagedelta):
		### this is fake for now, without using calibration
		rows = imagedelta[0]
		cols = imagedelta[1]
		stagex = 1e-7 * rows
		stagey = 1e-7 * cols
		return (stagex, stagey)

if __name__ == '__main__':
	id = ('navigator',)
	n = Navigator(id, None)
