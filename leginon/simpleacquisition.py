#!/usr/bin/env python

import node
import event
import data
import time
import cameraimage
import camerafuncs
import presets
import threading

class SimpleAcquisition(node.Node):
	def __init__(self, id, nodelocations, **kwargs):
		node.Node.__init__(self, id, nodelocations, **kwargs)

		self.cam = camerafuncs.CameraFuncs(self)
		self.presetsclient = presets.PresetsClient(self)

		self.loopstop = threading.Event()
		self.looplock = threading.Lock()

		self.defineUserInterface()
		self.start()

	def setPreset(self):
		presetname = self.presetname.get()
		print 'going to preset %s' % (presetname,)
		self.preset = self.presetsclient.getPreset(presetname)
		print 'preset mag:', self.preset['magnification']
		self.presetsclient.toScope(self.preset)
		time.sleep(2)

	def acquireImage(self):
		print 'acquiring image'
		acqtype = self.acqtype.get()
		if acqtype == 'raw': imagedata = self.cam.acquireCameraImageData(None,0)
		elif acqtype == 'corrected':
			try:
				imagedata = self.cam.acquireCameraImageData(camstate,1)
			except:
				print 'image not acquired'
				imagedata = None

		if imagedata is None:
			return
		## attach preset to imagedata
		imagedata.content['preset'] = dict(self.preset)

		print 'publishing image'
		self.publish(imagedata, event.CameraImagePublishEvent)
		print 'image published'

	def acquireImageOne(self):
		self.setPreset()
		self.acquireImage()
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
		self.setPreset()
		self.loopstop.clear()
		while 1:
			if self.loopstop.isSet():
				break
			self.acquireImage()
			time.sleep(pausetime)
		try:
			self.looploock.release()
		except:
			pass

	def acquireImageLoopStop(self):
		self.loopstop.set()
		return ''

	def defineUserInterface(self):
		nodeui = node.Node.defineUserInterface(self)

		acqtypes = self.registerUIData('acqtypes', 'array', default=('raw', 'corrected'))
		self.acqtype = self.registerUIData('Acquisition Type', 'string', default='raw', permissions='rw', choices=acqtypes)

		self.presetname = self.registerUIData('Preset Name', 'string', default='p56', permissions='rw')

		prefs = self.registerUIContainer('Preferences', (self.acqtype,self.presetname))

		acq = self.registerUIMethod(self.acquireImageOne, 'Acquire', ())
		pausetime = self.registerUIData('Pause Time', 'float', default=0)
		acqloop = self.registerUIMethod(self.acquireImageLoop, 'Acquire Loop', (pausetime,))
		acqloopstop = self.registerUIMethod(self.acquireImageLoopStop, 'Stop', ())
		acqcont = self.registerUIContainer('Acquire', (acq, acqloop, acqloopstop))

		self.registerUISpec('Simple Acquisition', (acqcont, prefs, nodeui))

