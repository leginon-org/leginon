#!/usr/bin/env python

import imagewatcher
import Numeric

import ImageViewer
import threading
from Tkinter import *
import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib
import camerafuncs
import Mrc
import node, data, event

class ImViewer(imagewatcher.ImageWatcher):
	def __init__(self, id, nodelocations, **kwargs):
		imagewatcher.ImageWatcher.__init__(self, id, nodelocations, **kwargs)

		self.cam = camerafuncs.CameraFuncs(self)

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 500
		self.cam.config(currentconfig)

		self.viewer_ready = threading.Event()
		self.clicklock = threading.Lock()

		self.defineUserInterface()
		self.start()

	def processData(self, imagedata):
		imagewatcher.ImageWatcher.processData(self, imagedata)
		if self.popupvalue:
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
			pass

	def clickEventCallback(self, tkevent):
		if not self.clicklock.acquire(0):
			print 'locked'
			return
		try:
			clickinfo = self.iv.eventXYInfo(tkevent)
			print 'CLICKINFO', clickinfo
			imageinfo = self.imageInfo()
			clickinfo.update(imageinfo)
			e = event.ImageClickEvent(self.ID(), clickinfo)
			self.outputEvent(e)
		finally:
			self.clicklock.release()

	def clickEventOn(self):
		self.iv.bindCanvas('<Double-1>', self.clickEventCallback)

	def clickEventOff(self):
		self.iv.bindCanvas('<Double-1>', '')

	def uiAcquireRaw(self):
		imarray = self.acquireArray(0)
		if imarray is None:
			mrcstr = ''
		else:
			mrcstr = Mrc.numeric_to_mrcstr(imarray)
		return xmlbinlib.Binary(mrcstr)

	def uiAcquireCorrected(self):
		im = self.acquireArray(1)
		if im is None:
			mrcstr = ''
		else:
			mrcstr = Mrc.numeric_to_mrcstr(im)
		return xmlbinlib.Binary(mrcstr)

	def acquireArray(self, corr=0):
		camconfig = self.cam.config()
		camstate = camconfig['state']
		imdata = self.cam.acquireCameraImageData(camstate, correction=corr)
		#imarray = imdata.content['image']
		imarray = imdata['image']
		return imarray

	def acquireAndDisplay(self, corr=0):
		print 'acquireArray'
		imarray = self.acquireArray(corr)
		print 'displayNumericArray'
		if imarray is None:
			self.iv.displayMessage('NO IMAGE ACQUIRED')
		else:
			self.displayNumericArray(imarray)
		print 'acquireAndDisplay done'

	def acquireEvent(self):
		e = event.ImageAcquireEvent(self.ID())
		self.outputEvent(e)
		return ''

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

	def popupCallback(self, value=None):
		if value is not None:
			self.popupvalue = value

		if self.popupvalue:
			self.displayNumericArray()
		
		return self.popupvalue

	def uiLoadImage(self, filename):
		self.numarray = Mrc.mrc_to_numeric(filename)
		self.displayNumericArray()
		return ''

	def uiSaveImage(self, filename):
		numarray = Numeric.array(self.iv.imagearray)
		Mrc.numeric_to_mrc(numarray, filename)
		return ''

	def defineUserInterface(self):
		watcherspec = imagewatcher.ImageWatcher.defineUserInterface(self)

		argspec = (
		self.registerUIData('Filename', 'string', default='test1.mrc'),
		)
		loadspec = self.registerUIMethod(self.uiLoadImage, 'Load MRC', argspec)
		savespec = self.registerUIMethod(self.uiSaveImage, 'Save MRC', argspec)
		filespec = self.registerUIContainer('File', (loadspec,savespec))

		acqret = self.registerUIData('Image', 'binary')

		acqraw = self.registerUIMethod(self.uiAcquireRaw, 'Acquire Raw', (), returnspec=acqret)
		acqcor = self.registerUIMethod(self.uiAcquireCorrected, 'Acquire Corrected', (), returnspec=acqret)
		acqev = self.registerUIMethod(self.acquireEvent, 'Acquire Event', ())

		popupdefault = xmlrpclib.Boolean(1)
		popuptoggle = self.registerUIData('Pop-up Viewer', 'boolean', permissions='rw', default=popupdefault)
		popuptoggle.registerCallback(self.popupCallback)

		camconfig = self.cam.configUIData()
		prefs = self.registerUIContainer('Preferences', (popuptoggle, camconfig,))

		myspec = self.registerUISpec(`self.id`, (acqraw, acqcor, acqev, prefs, filespec))
		myspec += watcherspec
		return myspec
