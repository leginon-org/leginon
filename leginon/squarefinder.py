#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import data
from imagefun import TooManyBlobs
import Mrc
import squarefinderback
import targetfinder
import uidata

class SquareFinder(targetfinder.TargetFinder):
	def __init__(self, id, session, nodelocations, **kwargs):
		targetfinder.TargetFinder.__init__(self, id, session, nodelocations,
																				**kwargs)
		self.squarefinder = squarefinderback.SquareFinder()
		self.image = None
		self.defineUserInterface()
		self.setImage(None)
		self.start()

	def setImage(self, image):
		self.image = image
		self.ui_image.setImage(self.image)
		if self.image is not None:
			dimension = self.uisquaredimension.get()
			if dimension is not None:
				self.updateMaxBlobs(self.image, dimension)
			self.lpfmethod.enable()
		else:
			self.lpfmethod.disable()
		self.setLPFImage(None)
		self.blobs = []
		self.targets = []
		self.squaredimension = None

	def setLPFImage(self, image):
		self.lpfimage = image
		if self.lpfimage is not None:
			self.ui_image.setImage(self.lpfimage)
			self.thresholdmethod.enable()
		else:
			self.thresholdmethod.disable()
		self.setThresholdImage(None)

	def setThresholdImage(self, image):
		self.thresholdimage = image
		if self.thresholdimage is not None:
			self.ui_image.setImage(self.thresholdimage)
			self.findblobsmethod.enable()
		else:
			self.findblobsmethod.disable()
		self.setBlobs([])

	def setBlobs(self, blobs):
		self.blobs = blobs
		if blobs:
			self.targetmethod.enable()
		else:
			self.targetmethod.disable()
		self.setTargets([])

	def setTargets(self, targets):
		self.targets = targets
		self.ui_image.setTargetType('Targets', self.targets)

	def lowPassFilter(self):
		size = self.uilpfsize.get()
		sigma = self.uilpfsigma.get()
		try:
			image = self.squarefinder.lowPassFilter(size, sigma, self.image)
		except (RuntimeError, OverflowError):
			image = None
			self.messagelog.error('Low pass filter failed')
		self.setLPFImage(image)

	def threshold(self):
		self.setThresholdImage(self.squarefinder.threshold(self.lpfimage))

	def findBlobs(self):
		border = self.uiborder.get()
		maxblobs = self.uimaxblobs.get()
		maxblobsize = self.uimaxblobsize.get()
		try:
			blobs = self.squarefinder.findblobs(self.lpfimage, self.thresholdimage,
																					border, maxblobs, maxblobsize)
		except TooManyBlobs:
			blobs = []
			self.messagelog.error('Too many blobs found')
		self.setBlobs(blobs)

	def target(self):
		targetborder = self.uitargetborder.get()
		shape = self.image.shape
		if targetborder < 0 or targetborder > shape[0]/2 \
				or targetborder > shape[1]/2:
			self.messagelog.error('Invalid border size specified')
		targetmin = (targetborder, targetborder)
		targetmax = (self.image.shape[0] - targetborder,
									self.image.shape[1] - targetborder)
		targets = []
		for blob in self.blobs:
			if blob[0] >= targetmin[0] and blob[0] <= targetmax[0] \
					and blob[1] >= targetmin[1] and blob[1] <= targetmax[1]:
				targets.append(blob)
		self.setTargets(targets)

	def uiLoad(self):
		filename = self.uitestfilename.get()
		try:
			image = Mrc.mrc_to_numeric(filename)
		except IOError:
			image = None
			self.messagelog.error('Load file "%s" failed' % filename)
		self.setImage(image)

	def uiLowPassFilter(self):
		self.lowPassFilter()

	def uiThreshold(self):
		self.threshold()

	def uiFindBlobs(self):
		self.findBlobs()

	def uiTarget(self):
		self.target()

	def onSetSquareDimension(self, value):
		if value is None:
			return value
		if self.image is not None:
			self.updateMaxBlobs(self.image, value)
		self.uimaxblobsize.set((value*1.1)**2)
		self.uitargetborder.set(value/2)
		return value

	def updateMaxBlobs(self, image, dimension):
		maxblobs = image.shape[0]/dimension * image.shape[1]/dimension
		self.uimaxblobs.set(maxblobs)

	def onShowAdvanced(self, value):
		if value:
			self.advancedcontainer.enable()
		else:
			self.advancedcontainer.disable()
		return value

	def defineUserInterface(self):
		targetfinder.TargetFinder.defineUserInterface(self)
		self.uidataqueueflag.set(False)

		self.messagelog = uidata.MessageLog('Message Log')

		self.ui_image = uidata.TargetImage('Image', None, 'r')

		self.uitestfilename = uidata.String('Test filename', None, 'rw',
																				persist=True)
		self.loadmethod = uidata.Method('Load', self.uiLoad)
		testfilecontainer = uidata.Container('Test File')
		testfilecontainer.addObjects((self.uitestfilename, self.loadmethod))

		self.uilpfsize = uidata.Number('Size', 5, 'rw',
																		persist=True)
		self.uilpfsigma = uidata.Number('Sigma', 1.4, 'rw',
																		persist=True)
		self.lpfmethod = uidata.Method('Low Pass Filter', self.uiLowPassFilter)
		self.lpfmethod.disable()
		lpfcontainer = uidata.Container('Low Pass Filter')
		lpfcontainer.addObjects((self.uilpfsize, self.uilpfsigma))

		self.thresholdmethod = uidata.Method('Threshold', self.uiThreshold)
		self.thresholdmethod.disable()

		self.ui_image.addTargetType('Targets')
		self.uiborder = uidata.Number('Border', 0, 'rw', persist=True)
		self.uimaxblobs = uidata.Number('Maximum Blobs', 100, 'rw', persist=True)
		self.uimaxblobsize = uidata.Number('Maximum Blob Size', 250, 'rw',
																				persist=True)
		self.findblobsmethod = uidata.Method('Find Blobs', self.uiFindBlobs)
		self.findblobsmethod.disable()
		findblobscontainer = uidata.Container('Find Blobs')
		findblobscontainer.addObjects((self.uiborder, self.uimaxblobs,
																		self.uimaxblobsize))

		self.uitargetborder = uidata.Number('Border', 0, 'rw', persist=True)
		self.targetmethod = uidata.Method('Target', self.uiTarget)
		self.targetmethod.disable()
		targetcontainer = uidata.Container('Targets')
		targetcontainer.addObjects((self.uitargetborder,))

		self.uisquaredimension = uidata.Number('Square Dimension', None, 'rw',
															callback=self.onSetSquareDimension, persist=True)

		self.advancedcontainer = uidata.Container('Advanced')
		self.advancedcontainer.addObjects((lpfcontainer, findblobscontainer,
																	targetcontainer))
		self.uishowadvanced = uidata.Boolean('Edit advanced settings', False, 'rw',
																					callback=self.onShowAdvanced,
																					persist=True)
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObjects((self.uisquaredimension, self.uishowadvanced,
																	self.advancedcontainer))

		controlcontainer = uidata.Container('Control')
		controlcontainer.addObjects((self.lpfmethod, self.thresholdmethod,
																	self.findblobsmethod, self.targetmethod))

		container = uidata.LargeContainer('Square Finder')
		container.addObjects((self.messagelog, testfilecontainer,
													settingscontainer, controlcontainer,
													self.ui_image,))
		self.uiserver.addObjects((container,))

