#!/usr/bin/env python

import event
import data
import time
import cameraimage
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

		acq = uidata.UIMethod('Acquire', self.acquireImageOne)
		self.pausetime = uidata.UIFloat('Pause Time', 0.0, 'rw')

		acqloop = uidata.UIMethod('Acquire Loop', self.acquireImageLoop)
		acqloopstop = uidata.UIMethod('Stop', self.acquireImageLoopStop)

		acqcont = uidata.UIMediumContainer('Acquire')
		acqcont.addUIObjects((acq, acqloop, acqloopstop))

		container = uidata.UIMediumContainer('Simple Acquisition')
		container.addUIObject(acqcont)
		self.uiserver.addUIObject(container)
