#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue

class TargetFinder(imagewatcher.ImageWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, nodelocations, **kwargs)

	def findTargets(self, numarray):
		'''
		this should either publish a list of targets, or publish
		each of them as they are chosen 
		'''
		raise NotImplementedError()

	def processData(self, newdata):
		imagewatcher.ImageWatcher.processData(self, newdata)

		numdata = newdata.content['image']
		self.findTargets(numdata)

	def defineUserInterface(self):
		imwatch = imagewatcher.ImageWatcher.defineUserInterface(self)
		## turn on data queue by default
		self.dataqueuetoggle.set(1)
		return imwatch


class ClickTargetFinder(TargetFinder):
	def __init__(self, id, nodelocations, **kwargs):
		watchfor = event.CameraImagePublishEvent
		lockblocking = None
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking, **kwargs)

	def findTargets(self, numarray):
		'''
		wait for the user to finish editing the targets
		'''
		pass

	def defineUserInterface(self):
		tfspec = TargetFinder.defineUserInterface(self)

		next = self.registerUIMethod(self.uiNext, 'Next', ())
		submit = self.registerUIMethod(self.uiSubmit, 'Submit', ())

		myspec = self.registerUISpec('Click Target Finder', (next,))
		myspec += tfspec

	def uiNext(self):
		self.processDataFromQueue()
		return ''

	def uiSubmit(self):
		return ''
