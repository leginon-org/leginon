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
import presets
import threading
import acquisition
import uidata
import node

class SimpleAcquisition(acquisition.Acquisition):
	'''
	SimpleAcquisition does not take targets, it just acquires images
	at the users command
	'''
	def __init__(self, id, session, nodelocations, **kwargs):
		self.loopstop = threading.Event()

		acquisition.Acquisition.__init__(self, id, session, nodelocations, **kwargs)

	def acquireImageOne(self):
		self.processTargetData(None)
		node.beep()
		return ''

	def acquireImageOneNoPreset(self):
		self.acquire(None)
		node.beep()

	def alreadyAcquired(self, targetdata, presetname):
		'''
		override so that an image is never 'alreadyAcquired'
		(because targetdata will always be none)
		'''
		return False

	def acquireImageLoop(self):
		t = threading.Thread(target=self.loop)
		t.setDaemon(1)
		t.start()
		return ''

	def loop(self):
		## would be nice if only set preset at beginning
		## need to change Acquisition to do that as option
		self.loopstop.clear()
		while 1:
			if self.loopstop.isSet():
				break
			self.processTargetData(None)
			time.sleep(self.pausetime.get())
		print 'loop done'

	def acquireImageLoopStop(self):
		print 'will stop loop when this iteration completes'
		self.loopstop.set()
		return ''

	def defineUserInterface(self):
		acquisition.Acquisition.defineUserInterface(self)

		acq = uidata.Method('Acquire Using Presets', self.acquireImageOne)
		acqnopreset = uidata.Method('Acquire - No Presets', self.acquireImageOneNoPreset)
		self.pausetime = uidata.Float('Pause Time (sec)', 0.0, 'rw', persist=True)

		acqloop = uidata.Method('Acquire Loop', self.acquireImageLoop)
		acqloopstop = uidata.Method('Stop', self.acquireImageLoopStop)

		acqcont = uidata.Container('Acquire')
		acqcont.addObjects((acq, acqnopreset, acqloop, self.pausetime, acqloopstop))

		container = uidata.LargeContainer('Simple Acquisition')
		container.addObject(acqcont)
		self.uicontainer.addObject(container)

