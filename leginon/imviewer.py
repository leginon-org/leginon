#!/usr/bin/env python

import imagewatcher
import Numeric

import ImageViewer
import threading
from Tkinter import *
import camerafuncs
import Mrc
import node, data, event
import uidata

class ImViewer(imagewatcher.ImageWatcher):
	def __init__(self, id, session, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, session, nodelocations, **kwargs)
		self.cam = camerafuncs.CameraFuncs(self)

		self.viewer_ready = threading.Event()
		self.clicklock = threading.Lock()

		self.defineUserInterface()
		self.start()

	def processData(self, imagedata):
		imagewatcher.ImageWatcher.processData(self, imagedata)
		self.ui_image.set(self.numarray)
		if self.uipopupflag.get():
			self.displayNumericArray()

	def die(self, ievent=None):
		self.close_viewer()
		imagewatcher.ImageWatcher.die(self)

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name=`self.id`, target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		#print 'thread started'

	def open_viewer(self):
		#print 'root...'
		root = self.root = Toplevel()
		## this gets rid of the root window
		root._root().withdraw()
		
		#root.wm_sizefrom('program')
		root.wm_geometry('=450x400')

		self.iv = ImageViewer.ImageViewer(root, bg='#488')
		self.iv.pack()

		self.viewer_ready.set()
		root.mainloop()

		##clean up if window destroyed
		self.viewer_ready.clear()
		self.iv = None

	def close_viewer(self):
		try:
			self.root.destroy()
		except:
			### root may not exist or already destroyed
			self.printException()

	def clickEventCallback(self, tkevent):
		if not self.clicklock.acquire(0):
			print 'locked'
			return
		try:
			clickinfo = self.iv.eventXYInfo(tkevent)
			print 'CLICKINFO', clickinfo
			imageinfo = self.imageInfo()
			clickinfo.update(imageinfo)
			e = event.ImageClickEvent(id=self.ID(), initializer=clickinfo)
			self.outputEvent(e)
		finally:
			self.clicklock.release()

	def clickEventOn(self):
		self.iv.bindCanvas('<Double-1>', self.clickEventCallback)

	def clickEventOff(self):
		self.iv.bindCanvas('<Double-1>', '')

	def uiAcquireRaw(self):
		imarray = self.acquireArray(0)
		if imarray is not None:
			self.ui_image.set(imarray)

	def uiAcquireCorrected(self):
		imarray = self.acquireArray(1)
		if imarray is not None:
			self.ui_image.set(imarray)

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

	def displayNumericArray(self):
		'''
		display the current self.numarray in the popup viewer
		'''
		self.start_viewer_thread()
		self.viewer_ready.wait()
		if self.numarray is not None:
			self.iv.import_numeric(self.numarray)
			self.iv.update()
		self.clickEventOn()

	def popupCallback(self, value):
		if value:
			self.displayNumericArray()
#		else:
#			self.close_viewer()
		return value

	def uiLoadImage(self):
		filename = self.uifilename.get()
		self.numarray = Mrc.mrc_to_numeric(filename)
		self.ui_image.set(self.numarray)
		if self.uipopupflag.get():
			self.displayNumericArray()

	def uiSaveImage(self):
		filename = self.uifilename.get()
		numarray = Numeric.array(self.iv.imagearray)
		Mrc.numeric_to_mrc(numarray, filename)

	def defineUserInterface(self):
		imagewatcher.ImageWatcher.defineUserInterface(self)
		self.uifilename = uidata.UIString('Filename', '', 'rw')
		loadmethod = uidata.UIMethod('Load MRC', self.uiLoadImage)
		savemethod = uidata.UIMethod('Save MRC', self.uiSaveImage)
		filecontainer = uidata.UIContainer('File')
		filecontainer.addUIObjects((self.uifilename, loadmethod, savemethod))

		self.ui_image = uidata.UIImage('Image', None, 'r')
		rawmethod = uidata.UIMethod('Acquire Raw', self.uiAcquireRaw)
		correctedmethod = uidata.UIMethod('Acquire Corrected',
																			self.uiAcquireCorrected)
		eventmethod = uidata.UIMethod('Event Acquire', self.acquireEvent)
		acquirecontainer = uidata.UIContainer('Acquisition')
		acquirecontainer.addUIObjects((self.ui_image, rawmethod, correctedmethod,
																		eventmethod))

		self.uipopupflag = uidata.UIBoolean('Pop-up Viewer', False, 'rw',
																				self.popupCallback)
		cameraconfigure = self.cam.configUIData()
		settingscontainer = uidata.UIContainer('Settings')
		settingscontainer.addUIObjects((self.uipopupflag, cameraconfigure))

		container = uidata.UIMediumContainer('Image Viewer')
		container.addUIObjects((acquirecontainer, settingscontainer, filecontainer))

		self.uiserver.addUIObject(container)

