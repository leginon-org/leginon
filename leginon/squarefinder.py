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
		self.lpfimage = None
		self.thresholdimage = None
		self.blobs = []
		self.targets = []
		self.defineUserInterface()
		self.start()

	def lowPassFilter(self):
		size = self.uilpfsize.get()
		sigma = self.uilpfsigma.get()
		try:
			self.lpfimage = self.squarefinder.lowPassFilter(size, sigma, self.image)
		except (RuntimeError, OverflowError):
			self.messagelog.error('Low pass filter failed')
			return
		self.thresholdmethod.enable()

	def threshold(self):
		self.thresholdimage = self.squarefinder.threshold(self.lpfimage)
		self.findblobsmethod.enable()

	def findBlobs(self):
		border = self.uiborder.get()
		maxblobs = self.uimaxblobs.get()
		maxblobsize = self.uimaxblobsize.get()
		try:
			self.blobs = self.squarefinder.findblobs(self.lpfimage,
																										self.thresholdimage, border,
																										maxblobs, maxblobsize)
		except TooManyBlobs:
			self.messagelog.error('Too many blobs found')
			return
		self.targetmethod.enable()

	def target(self):
		self.targets = []
		targetborder = self.uitargetborder.get()
		shape = self.image.shape
		if targetborder < 0 or targetborder > shape[0]/2 \
				or targetborder > shape[1]/2:
			self.messagelog.error('Invalid border size specified')
		targetmin = (targetborder, targetborder)
		targetmax = (self.image.shape[0] - targetborder,
									self.image.shape[1] - targetborder)
		for blob in self.blobs:
			if blob[0] >= targetmin[0] and blob[0] <= targetmax[0] \
					and blob[1] >= targetmin[1] and blob[1] <= targetmax[1]:
				self.targets.append(blob)

	def uiLoad(self):
		filename = self.uitestfilename.get()
		try:
			self.image = Mrc.mrc_to_numeric(filename)
		except IOError:
			self.messagelog.error('Load file "%s" failed' % filename)
			return
		self.ui_image.setImage(self.image)
		self.lpfmethod.enable()

	def uiLowPassFilter(self):
		self.lowPassFilter()
		self.ui_image.setImage(self.lpfimage)

	def uiThreshold(self):
		self.threshold()
		self.ui_image.setImage(self.thresholdimage)

	def uiFindBlobs(self):
		self.findBlobs()

	def uiTarget(self):
		self.target()
		self.ui_image.setTargetType('Targets', self.targets)

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
		self.lpfmethod = uidata.Method('Smooth', self.uiLowPassFilter)
		self.lpfmethod.disable()
		lpfcontainer = uidata.Container('Low Pass Filter')
		lpfcontainer.addObjects((self.uilpfsize, self.uilpfsigma, self.lpfmethod))

		self.thresholdmethod = uidata.Method('Threshold', self.uiThreshold)
		self.thresholdmethod.disable()
		thresholdcontainer = uidata.Container('Threshold')
		thresholdcontainer.addObjects((self.thresholdmethod,))

		self.ui_image.addTargetType('Targets')
		self.uiborder = uidata.Number('Border', 0, 'rw', persist=True)
		self.uimaxblobs = uidata.Number('Maximum Blobs', 100, 'rw', persist=True)
		self.uimaxblobsize = uidata.Number('Maximum Blob Size', 250, 'rw',
																				persist=True)
		self.findblobsmethod = uidata.Method('Find Blobs', self.uiFindBlobs)
		self.findblobsmethod.disable()
		findblobscontainer = uidata.Container('Find Blobs')
		findblobscontainer.addObjects((self.uiborder, self.uimaxblobs,
																		self.uimaxblobsize, self.findblobsmethod))

		self.uitargetborder = uidata.Number('Border', 0, 'rw', persist=True)
		self.targetmethod = uidata.Method('Target', self.uiTarget)
		self.targetmethod.disable()
		targetcontainer = uidata.Container('Targets')
		targetcontainer.addObjects((self.uitargetborder, self.targetmethod))

		container = uidata.LargeContainer('Square Finder')
		container.addObjects((self.messagelog, testfilecontainer, lpfcontainer,
													thresholdcontainer, findblobscontainer,
													targetcontainer, self.ui_image,))
		self.uiserver.addObjects((container,))

