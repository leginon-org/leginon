#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue
import Mrc

import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

# TO DO:
#  - every TargetFinder should have optional target editing before publishing
#  - a lot of work to reorganize this class hierarchy
#       - everything to do with ImageTargetData should be in this module
#               (not in imagewatcher)

class TargetFinder(imagewatcher.ImageWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, nodelocations, **kwargs)

	def findTargets(self, numarray):
		'''
		this should build self.targetlist, a list of 
		ImageTargetData items.
		'''
		raise NotImplementedError()

	def processData(self, newdata):
		imagewatcher.ImageWatcher.processData(self, newdata)

		print 'findTargets'
		self.findTargets(newdata)
		print 'publishTargets'
		self.publishTargetList()
		print 'DONE'

	def publishTargetList(self):

		if self.targetlist:
			targetlistdata = data.ImageTargetListData(self.ID(), self.targetlist)
			self.publish(targetlistdata, event.ImageTargetListPublishEvent)
			print 'published targetlistdata', targetlistdata
			print 'content'
			print targetlistdata.content

	def defineUserInterface(self):
		imwatch = imagewatcher.ImageWatcher.defineUserInterface(self)
		## turn on data queue by default
		self.dataqueuetoggle.set(1)
		return imwatch


class ClickTargetFinder(TargetFinder):
	def __init__(self, id, nodelocations, **kwargs):
		TargetFinder.__init__(self, id, nodelocations, **kwargs)

		self.userbusy = threading.Condition()
		self.processlock = threading.Lock()
		self.currentimage = None

		self.defineUserInterface()
		self.start()

	def processData(self, newdata):
		'''
		redefined because this is manual target finding
		Instead of calling findTargets, let uiImage get the image
		Then call publishTargetList in another function
		'''
		imagewatcher.ImageWatcher.processData(self, newdata)
		
	def defineUserInterface(self):
		tfspec = TargetFinder.defineUserInterface(self)

		clickimage = self.registerUIData('Clickable Image', 'binary', callback=self.uiImage, permissions='rw')
		# this is just a placeholder for the argspec.  The real value
		# comes from clickimage which is the choices

		myspec = self.registerUISpec('Click Target Finder', (clickimage,))
		myspec += tfspec
		return myspec

	def uiImage(self, value=None):
		'''
		get next image from queue
		'''
		if value is None:
			if self.currentimage is None:
				if self.processDataFromQueue():
					self.currentimage = self.numarray
				else:
					self.currentimage = None

			if self.currentimage is None:
				mrcstr = ''
			else:
				mrcstr = Mrc.numeric_to_mrcstr(self.currentimage)

			return xmlbinlib.Binary(mrcstr)
		else:
			self.submitTargets(value)
			return xmlbinlib.Binary('')

	def submitTargets(self, targetlist):
		self.targetlist = []
		for target in targetlist:
			### attach some image info about this one
			imageinfo = self.imageInfo()
			target.update(imageinfo)
			print 'TARGET', target
			targetdata = data.ImageTargetData(self.ID(), target)
			self.targetlist.append(targetdata)
		self.publishTargetList()
		self.currentimage = None

	def OLDuiNext(self):
		if not self.processlock.acquire(0):
			return
		try:
			t = threading.Thread(target=self.processDataFromQueue)
			t.setDaemon(1)
			t.start()
		finally:
			self.processlock.release()

		return ''
