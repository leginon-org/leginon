#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
import signal

import ImageViewer

import watcher
import node, event, data
import Mrc
import cameraimage
import camerafuncs
import xmlrpclib
#import xmlrpclib2 as xmlbinlib
xmlbinlib = xmlrpclib

class ImViewer(watcher.Watcher):
	def __init__(self, id, nodelocations, **kwargs):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking, **kwargs)
		self.addEventOutput(event.ImageClickEvent)

		self.cam = camerafuncs.CameraFuncs(self)
		self.iv = None
		self.numarray = None
		self.imageid = None
		self.viewer_ready = threading.Event()
		#self.start_viewer_thread()

		## default camera config
		currentconfig = self.cam.config()
		currentconfig['state']['dimension']['x'] = 1024
		currentconfig['state']['binning']['x'] = 4
		currentconfig['state']['exposure time'] = 100

		self.clickfuncs = {
			'event': self.clickEvent,
			'target': self.clickTarget
		}

		self.cam.config(currentconfig)
		self.defineUserInterface()
		self.start()

	def die(self, ievent=None):
		self.close_viewer()
		watcher.Watcher.die(self)

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name=`self.id`, target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		#print 'thread started'

	def clickCallback(self, tkevent):
		clickinfo = self.iv.eventXYInfo(tkevent)
		clickinfo['image id'] = self.imageid

		choice = self.uiclickcallback.get()
		if choice == 'event':
			print 'clickEvent'
			self.clickEvent(clickinfo)
		elif choice == 'target':
			print 'clickTarget'
			self.clickTarget(clickinfo)

	def clickTarget(self, clickinfo):
		'''
		publish target when image clicked
		'''
		c = dict(clickinfo)
		c['source'] = 'click'
		print 'creating targetdata'
		targetdata = data.ImageTargetData(self.ID(), c)
		print 'publishing targetdata'
		self.publish(targetdata, event.ImageTargetPublishEvent)

	def clickEvent(self, clickinfo):
		'''
		generate ImageClickEvent when image clicked
		'''
		c = {}
		for key,value in clickinfo.items():
			if value is not None:
				c[key] = value
		e = event.ImageClickEvent(self.ID(), c)
		self.outputEvent(e)

	def open_viewer(self):
		#print 'root...'
		root = self.root = Toplevel()
		## this gets rid of the root window
		root._root().withdraw()
		
		#root.wm_sizefrom('program')
		root.wm_geometry('=450x400')

		self.iv = ImageViewer.ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.clickCallback)
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
		imarray = imdata.content['image']
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

	def processData(self, imagedata):
		#camdict = imagedata.content
		#imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		#width = camdict['x dimension']
		#height = camdict['y dimension']
		#numarray = Numeric.array(imarray)
		#numarray.shape = (height,width)

		c = imagedata.content
		self.numarray = c['image']

		self.imageid = imagedata.id
		print 'IMVIEWER', self.imageid, self.popupvalue
		if self.popupvalue:
			self.displayNumericArray()

	def displayNumericArray(self):
		self.start_viewer_thread()
		self.viewer_ready.wait()
		if self.numarray is not None:
			self.iv.import_numeric(self.numarray)
			self.iv.update()

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)

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

		clickchoices = self.registerUIData('clickfuncs', 'array', default=self.clickfuncs.keys())
		self.uiclickcallback = self.registerUIData('Click Callback', 'string', choices=clickchoices, default='event', permissions='rw')

		camconfig = self.cam.configUIData()
		prefs = self.registerUIContainer('Preferences', (popuptoggle, camconfig, self.uiclickcallback))

		self.registerUISpec(`self.id`, (acqraw, acqcor, acqev, prefs, filespec, watcherspec))

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



if __name__ == '__main__':
	id = ('ImViewer',)
	i = ImViewer(id, {})
	signal.pause()


