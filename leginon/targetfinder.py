#!/usr/bin/env python

import threading
import imagewatcher
import node, event, data
import Queue

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

		self.targetlist = []
		self.targetdict = {}

		print 'findTargets'
		self.findTargets(newdata)
		print 'publishTargets'
		self.publishTargetList()
		print 'DONE'

	def publishTargetList(self):
		if self.targetlist:
			targetlistdata = data.ImageTargetListData(self.ID(), self.targetlist)
			self.publish(targetlistdata, event.ImageTargetListPublishEvent)
		self.targetlist = []
		self.targetdict = {}

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

		self.defineUserInterface()
		self.start()

	def findTargets(self, newdata):
		'''
		wait for the user to finish editing the targets
		'''
		print 'waiting'
		self.userbusy.acquire()
		self.userbusy.wait()
		self.userbusy.release()

	def defineUserInterface(self):
		tfspec = TargetFinder.defineUserInterface(self)

		next = self.registerUIMethod(self.uiNext, 'Next', ())
		done = self.registerUIMethod(self.uiDone, 'Done', ())
		cont = self.registerUIContainer('Controls', (next, done))

		myspec = self.registerUISpec('Click Target Finder', (cont,))
		myspec += tfspec

	def processNext(self):
		try:
			self.processDataFromQueue()
		except Exception, detail:
			print 'DETAIL', detail
			raise

	def uiNext(self):
		if not self.processlock.acquire(0):
			return
		try:
			t = threading.Thread(target=self.processDataFromQueue)
			t.setDaemon(1)
			t.start()
		finally:
			self.processlock.release()

		return ''

	def uiDone(self):
		self.userbusy.acquire()
		self.userbusy.notify()
		self.userbusy.release()
		return ''
