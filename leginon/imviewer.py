#!/usr/bin/env python

import imagewatcher
import Numeric
import threading
import camerafuncs
import cameraimage
import Mrc
import node, data, event
import uidata

class ImViewer(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)
		self.clicklock = threading.Lock()
		self.defineUserInterface()
		self.start()

	def processData(self, imagedata):
		imagewatcher.ImageWatcher.processData(self, imagedata)
		self.ui_image.set(self.numarray)
		self.doPow()

	def doPow(self):
		if self.numarray is not None and self.do_pow.get():
			pow = cameraimage.power(self.numarray)
			self.ui_image_pow.set(pow)

	def uiAcquireRaw(self):
		imarray = self.acquireArray(0)
		if imarray is not None:
			self.numarray = imarray
			self.ui_image.set(imarray)
		self.doPow()

	def uiAcquireCorrected(self):
		imarray = self.acquireArray(1)
		if imarray is not None:
			self.numarray = imarray
			self.ui_image.set(imarray)
		self.doPow()

	def acquireArray(self, corr=0):
		camconfig = self.cam.cameraConfig()
		imdata = self.cam.acquireCameraImageData(camconfig, correction=corr)
		imarray = imdata['image']
		return imarray

#	def acquireAndDisplay(self, corr=0):
#		print 'acquireArray'
#		imarray = self.acquireArray(corr)
#		print 'displayNumericArray'
#		if imarray is None:
#			self.iv.displayMessage('NO IMAGE ACQUIRED')
#		else:
#			self.displayNumericArray(imarray)
#		print 'acquireAndDisplay done'

	def acquireEvent(self):
		e = event.ImageAcquireEvent(id=self.ID())
		self.outputEvent(e)

	def uiLoadImage(self):
		filename = self.uifilename.get()
		self.numarray = Mrc.mrc_to_numeric(filename)
		self.ui_image.set(self.numarray)
		self.doPow()

	def uiSaveImage(self):
		filename = self.uifilename.get()
		numarray = Numeric.array(self.iv.imagearray)
		Mrc.numeric_to_mrc(numarray, filename)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		self.uifilename = uidata.String('Filename', '', 'rw')
		loadmethod = uidata.Method('Load MRC', self.uiLoadImage)
		savemethod = uidata.Method('Save MRC', self.uiSaveImage)
		filecontainer = uidata.Container('File')
		filecontainer.addObjects((self.uifilename, loadmethod, savemethod))

		cameraconfigure = self.cam.configUIData()
		settingscontainer = uidata.Container('Settings')
		settingscontainer.addObject(cameraconfigure)

		rawmethod = uidata.Method('Acquire Raw', self.uiAcquireRaw)
		correctedmethod = uidata.Method('Acquire Corrected', self.uiAcquireCorrected)
		self.do_pow = uidata.Boolean('Do Power', False, 'rw')
		self.ui_image = uidata.Image('Image', None, 'r')
		self.ui_image_pow = uidata.Image('Power Image', None, 'r')
		eventmethod = uidata.Method('Event Acquire', self.acquireEvent)
		acquirecontainer = uidata.Container('Acquisition')
		acquirecontainer.addObjects((rawmethod, correctedmethod, eventmethod, self.do_pow, self.ui_image, self.ui_image_pow))


		container = uidata.MediumContainer('Image Viewer')
		container.addObjects((settingscontainer, filecontainer, acquirecontainer))

		self.uiserver.addObject(container)

