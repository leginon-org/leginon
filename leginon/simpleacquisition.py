#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import event
import data
import time
import camerafuncs
import presets
import threading
import acquisition
import uidata

class SimpleAcquisition(acquisition.Acquisition):
	'''
	SimpleAcquisition does not take targets, it just acquires images
	at the users command
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		self.loopstop = threading.Event()
		self.looplock = threading.Lock()

		acquisition.Acquisition.__init__(self, id, session, nodelocations, **kwargs)

	def acquireImageOne(self):
		self.processTargetData(None)
		return ''

	def alreadyAcquired(self, targetdata, presetname):
		'''
		override so that an image is never 'alreadyAcquired'
		(because targetdata will always be none)
		'''
		return False

	def acquireImageLoop(self):
		if not self.looplock.acquire(0):
			return
		try:
			t = threading.Thread(target=self.loop,args=(self.pausetime.get(),))
			t.setDaemon(1)
			t.start()
		except:
			try:
				self.looplock.release()
			except:
				pass
			raise
		return ''

	def loop(self, pausetime):
		## would be nice if only set preset at beginning
		## need to change Acquisition to do that as option
		self.loopstop.clear()
		while 1:
			if self.loopstop.isSet():
				break
			self.processTargetData(None)
			time.sleep(pausetime)
		try:
			self.looploock.release()
		except:
			pass

	def acquireImageLoopStop(self):
		self.loopstop.set()
		return ''

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)

		acq = uidata.Method('Acquire', self.acquireImageOne)
		self.pausetime = uidata.Float('Pause Time', 0.0, 'rw')

		acqloop = uidata.Method('Acquire Loop', self.acquireImageLoop)
		acqloopstop = uidata.Method('Stop', self.acquireImageLoopStop)

		acqcont = uidata.Container('Acquire')
		acqcont.addObjects((acq, acqloop, acqloopstop))

		container = uidata.LargeContainer('Simple Acquisition')
		container.addObject(acqcont)
		self.uiserver.addObject(container)

