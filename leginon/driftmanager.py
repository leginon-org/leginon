#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue
import Mrc
import uidata
import Numeric
import mosaic
import calibrationclient
import camerafuncs

import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

## this inherits imagewatcher because it watches for all acquisition images
class DriftManager(watcher.Watcher):
	eventinputs = watcher.Watcher.eventinputs + [event.DriftDetectedEvent, event.AcquisitionImagePublishEvent]
	eventoutputs = watcher.Watcher.eventoutputs + [event.DriftDoneEvent]
	def __init__(self, id, session, nodelocations, **kwargs):
		watchfor = [event.DriftDetected
		watcher.Watcher.__init__(self, id, session, nodelocations, watchfor, **kwargs)

	def processData(self, newdata):
		if isinstance(newdata, data.AcquisitionImageData):
			self.processImageData(newdata)
		if isinstance(newdata, data.AllEMData):
			self.processImageData(newdata)

	def processEMData(self, emdata):
		pass

	def processImageData(self, imagedata):
		# this should update my dictionary of most recent acquisitions
		self.references[

	def targetsToDatabase(self):
		for target in self.targetlist:
			self.publish(target, database=True)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		# turn on data queue by default
		self.uidataqueueflag.set(False)

		subcont = uidata.Container('Sub')

		container = uidata.MediumContainer('Drift Manager')
		container.addObjects(())
		self.uiserver.addObject(container)
