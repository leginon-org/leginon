#!/usr/bin/env python

import event
import data
import time
import cameraimage
import camerafuncs
import presets
import threading
import acquisition

class SimpleAcquisition(acquisition.Acquisition):
	'''
	SimpleAcquisition does not take targets, it just acquires images
	at the users command
	'''
	def __init__(self, id, nodelocations, **kwargs):
		self.loopstop = threading.Event()
		self.looplock = threading.Lock()

		acquisition.Acquisition.__init__(self, id, nodelocations, **kwargs)

	def acquireImageOne(self):
		'''
		this is same as Acquisition 'uiTrial'
		'''
		self.processTargetData()
		return ''

	def acquireImageLoop(self, pausetime):
		if not self.looplock.acquire(0):
			return
		try:
			t = threading.Thread(target=self.loop,args=(pausetime,))
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
			self.processTargetData()
			time.sleep(pausetime)
		try:
			self.looploock.release()
		except:
			pass

	def acquireImageLoopStop(self):
		self.loopstop.set()
		return ''

	def defineUserInterface(self):
		acqspec = acquisition.Acquisition.defineUserInterface(self)

		acq = self.registerUIMethod(self.acquireImageOne, 'Acquire', ())
		pausetime = self.registerUIData('Pause Time', 'float', default=0)
		acqloop = self.registerUIMethod(self.acquireImageLoop, 'Acquire Loop', (pausetime,))
		acqloopstop = self.registerUIMethod(self.acquireImageLoopStop, 'Stop', ())
		acqcont = self.registerUIContainer('Acquire', (acq, acqloop, acqloopstop))

		myspec = self.registerUISpec('Simple Acquisition', (acqcont,))
		myspec += acqspec
		return myspec

