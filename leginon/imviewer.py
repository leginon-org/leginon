#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
import signal, time

import ImageViewer
reload(ImageViewer)

import watcher
reload(watcher)
import node, event, data
import Mrc
import cameraimage
import camerafuncs
reload(camerafuncs)
import xmlrpclib

class ImViewer(watcher.Watcher, camerafuncs.CameraFuncs):
	def __init__(self, id, nodelocations):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)
		self.addEventOutput(event.ImageClickEvent)

		self.iv = None
		self.numarray = None
		self.viewer_ready = threading.Event()
		#self.start_viewer_thread()

	def die(self, killevent=None):
		self.close_viewer()
		self.exit()

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(name='image viewer thread', target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		#print 'thread started'

	def clickEvent(self, tkevent):
		clickinfo = self.iv.eventXYInfo(tkevent)
		clickinfo['image id'] = self.imageid
		#print 'clickinfo', clickinfo
		## prepare for xmlrpc
		c = {}
		for key,value in clickinfo.items():
			if value is not None:
				c[key] = value
		#print 'c', c
		e = event.ImageClickEvent(self.ID(), c)
		#print 'sending ImageClickEvent'
		self.outputEvent(e)
		#print 'sent ImageClickEvent'

	def open_viewer(self):
		#print 'root...'
		root = self.root = Tk()
		#root.wm_sizefrom('program')
		root.wm_geometry('=450x400')

		self.iv = ImageViewer.ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.clickEvent)
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
		return xmlrpclib.Binary(mrcstr)

	def uiAcquireCorrected(self):
		im = self.acquireArray(1)
		if im is None:
			mrcstr = ''
		else:
			mrcstr = Mrc.numeric_to_mrcstr(im)
		return xmlrpclib.Binary(mrcstr)

	def acquireArray(self, corr=0):
		camconfig = self.cameraConfig()
		camstate = camconfig['state']
		imarray = self.cameraAcquireArray(camstate, correction=corr)
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

		## self.im must be 2-d numeric data

		## this hack make ImViewer work with different imagedata types
		c = imagedata.content
		if type(c) is dict:
			self.numarray = c['image']
		else:
			self.numarray = c

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
		self.registerUIData('Filename', 'string'),
		)
		loadspec = self.registerUIMethod(self.uiLoadImage, 'Load MRC', argspec)
		savespec = self.registerUIMethod(self.uiSaveImage, 'Save MRC', argspec)
		filespec = self.registerUIContainer('File', (loadspec,savespec))

		acqret = self.registerUIData('Image', 'binary')

		acqraw = self.registerUIMethod(self.uiAcquireRaw, 'Acquire Raw', (), returnspec=acqret)
		acqcor = self.registerUIMethod(self.uiAcquireCorrected, 'Acquire Corrected', (), returnspec=acqret)
		acqev = self.registerUIMethod(self.acquireEvent, 'Acquire Event', ())

		popupdefault = xmlrpclib.Boolean(0)
		popuptoggle = self.registerUIData('Pop-up Viewer', 'boolean', permissions='rw', default=popupdefault)
		popuptoggle.registerCallback(self.popupCallback)

		camconfig = self.cameraConfigUIData()
		prefs = self.registerUIContainer('Preferences', (popuptoggle, camconfig))

		self.registerUISpec(`self.id`, (acqraw, acqcor, acqev, prefs, filespec, watcherspec))

	def popupCallback(self, value=None):
		if value is not None:
			self.popupvalue = value

		if self.popupvalue:
			self.displayNumericArray()
		
		return self.popupvalue

	def uiLoadImage(self, filename):
		im = Mrc.mrc_to_numeric(filename)
		self.displayNumericArray(im)
		return ''

	def uiSaveImage(self, filename):
		numarray = self.iv.imagearray
		Mrc.numeric_to_mrc(numarray, filename)
		return ''



if __name__ == '__main__':
	id = ('ImViewer',)
	i = ImViewer(id, {})
	signal.pause()


