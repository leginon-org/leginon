#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

import imagewatcher
import Numeric
import threading
import camerafuncs
import imagefun
import Mrc
import node, data, event
import uidata
import EM

class ImViewer(imagewatcher.ImageWatcher):
	eventinputs = imagewatcher.ImageWatcher.eventinputs + EM.EMClient.eventinputs
	eventoutputs = imagewatcher.ImageWatcher.eventoutputs + EM.EMClient.eventoutputs
	def __init__(self, id, session, managerlocation, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, managerlocation, **kwargs)

		self.emclient = EM.EMClient(self)
		self.cam = camerafuncs.CameraFuncs(self)
		self.clicklock = threading.Lock()
		self.looplock = threading.Lock()
		self.loopstop = threading.Event()
		self.loopconfig = False
		self.defineUserInterface()
		self.start()

	def processImageData(self, imagedata):
		self.ui_image.set(imagedata['image'])
		self.doPow()

	def doPow(self):
		maskrad = self.maskrad.get()
		if self.numarray is not None and self.do_pow.get():
			pow = imagefun.power(self.numarray, maskrad)
			self.ui_image_pow.set(pow)

	def uiAcquireLoop(self):
		if not self.looplock.acquire(0):
			return
		self.cam.uiApplyAsNeeded()
		try:
			t = threading.Thread(target=self.loop)
			t.setDaemon(1)
			t.start()
		except:
			try:
				self.looplock.release()
			except:
				pass
			raise
		return ''

	def loop(self):
		## would be nice if only set preset at beginning
		## need to change Acquisition to do that as option
		self.loopstop.clear()
		while 1:
			if self.loopstop.isSet():
				break
			try:
				self.uiAcquire()
			except:
				self.logger.exception('')
				break
		try:
			self.looplock.release()
		except:
			pass

	def uiAcquireLoopStop(self):
		self.loopstop.set()
		self.loopconfig = False
		return ''

	def uiAcquire(self):
		self.cam.uiApplyAsNeeded()
		imarray = self.acquireArray()
		if imarray is not None:
			self.numarray = imarray
			self.ui_image.set(imarray)
		self.doPow()

	def acquireArray(self):
		imdata = self.cam.acquireCameraImageData()
		imarray = imdata['image']
		return imarray

	def loadImage(self, filename):
		self.logger.info('Loading %s...' % filename)
		if filename is None:
			return
		try:
			self.numarray = Mrc.mrc_to_numeric(filename)
			self.logger.info('Image size %s' % (self.numarray.shape,))
			self.ui_image.set(self.numarray)
			self.logger.info('Performing FFT...')
			self.doPow()
			self.logger.info('FFT done')
		except (TypeError, IOError):
			self.logger.error('Unable to load image \'%s\'' % filename)

	def uiLoadImage(self):
		try:
			self.filecontainer.addObject(uidata.LoadFileDialog('Load Image',
																													self.loadImage))
		except ValueError:
			pass

	def saveImage(self, filename):
		numarray = self.numarray.copy()
		try:
			Mrc.numeric_to_mrc(numarray, filename)
		except (TypeError, IOError):
			self.logger.error('Unable to save image \'%s\'' % filename)

	def uiSaveImage(self):
		try:
			self.filecontainer.addObject(uidata.SaveFileDialog('Save Image',
																													self.saveImage))
		except ValueError:
			pass

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		savemethod = uidata.Method('Save', self.uiSaveImage)
		loadmethod = uidata.Method('Load', self.uiLoadImage)
		self.filecontainer = uidata.Container('File')
		self.filecontainer.addObjects((savemethod, loadmethod))

		cameraconfigure = self.cam.uiSetupContainer()
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObject(cameraconfigure)

		acqmethod = uidata.Method('Acquire', self.uiAcquire)
		acqloopmethod = uidata.Method('Acquire Loop', self.uiAcquireLoop)
		acqstopmethod = uidata.Method('Stop Acquire Loop', self.uiAcquireLoopStop)
		self.do_pow = uidata.Boolean('Do Power', False, 'rw')
		self.maskrad = uidata.Float('Power Mask Radius (% of image width)', 0.01, 'rw', persist=True)
		self.ui_image = uidata.Image('Image', None, 'r')
		self.ui_image_pow = uidata.Image('Power Image', None, 'r')
		acquirecontainer = uidata.Container('Acquisition')
		acquirecontainer.addObjects((acqmethod, acqloopmethod, acqstopmethod,
																	self.do_pow, self.maskrad, self.ui_image,
																	self.ui_image_pow))


		container = uidata.LargeContainer('Image Viewer')
		container.addObjects((settingscontainer, self.filecontainer,
													acquirecontainer))

		self.uicontainer.addObject(container)

