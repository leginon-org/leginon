#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
import signal, time

from ImageViewer import ImageViewer
import watcher
import node, event
from Mrc import mrc_to_numeric


class ImViewer(watcher.Watcher):
	def __init__(self, id, nodelocations):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

		self.addEventOutput(event.ImageClickEvent)

		self.iv = None
		self.viewer_ready = threading.Event()
		self.start_viewer_thread()

		self.print_location()

	def die(self, killevent):
		self.close_viewer()
		self.exit()

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		print 'thread started'

	def clickEvent(self, tkevent):
		clickinfo = self.iv.eventXYInfo(tkevent)
		clickinfo['image id'] = self.imageid
		print 'clickinfo', clickinfo
		## prepare for xmlrpc
		c = {}
		for key,value in clickinfo.items():
			if value is not None:
				c[key] = value
		print 'c', c
		e = event.ImageClickEvent(self.ID(), c)
		print 'sending ImageClickEvent'
		self.outputEvent(e)
		print 'sent ImageClickEvent'

	def open_viewer(self):
		print 'root...'
		root = self.root = Tk()
		root.wm_maxsize(800,800)
		print 'iv'
		self.iv = ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.clickEvent)
		print 'iv pack'
		self.iv.pack()
		print 'acqbut'
		self.acqeventbut = Button(root, text='Acquire Event', command=self.acquireEvent)
		self.acqeventbut.pack()
		self.acqbut = Button(root, text='Acquire', command=self.acquire)
		self.acqbut.pack()
		print 'viewer_ready.set'
		self.viewer_ready.set()
		print 'mainloop'
		root.mainloop()
		print 'viewer_ready.clear'
		self.viewer_ready.clear()
		print 'viewer_ready.cleared'
		self.iv = None

	def close_viewer(self):
		try:
			self.root.destroy()
		except TclError:
			pass

	def acquire(self):
		self.acqbut['state'] = DISABLED
		imdata = self.researchByDataID('image data')
		self.displayNumericArray(imdata['image data'])
		self.acqbut['state'] = NORMAL

	def acquireEvent(self):
		self.acqeventbut['state'] = DISABLED
		print 'sending ImageAcquireEvent'
		e = event.ImageAcquireEvent(self.ID())
		print 'e', e
		self.outputEvent(e)
		print 'sent ImageAcquireEvent'
		self.acqeventbut['state'] = NORMAL
	
	def processData(self, imagedata):
		#camdict = imagedata.content
		#imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		#width = camdict['x dimension']
		#height = camdict['y dimension']
		#numarray = Numeric.array(imarray)
		#numarray.shape = (height,width)

		## self.im must be 2-d numeric data

		self.start_viewer_thread()

		numarray = imagedata.content
		self.imageid = imagedata.id
		self.displayNumericArray(numarray)

	def displayNumericArray(self, numarray):
		self.start_viewer_thread()
		self.viewer_ready.wait()
		self.iv.import_numeric(numarray)
		self.iv.update()

	def defineUserInterface(self):
		watcherspec = watcher.Watcher.defineUserInterface(self)

		argspec = (
		self.registerUIData('Filename', 'string'),
		)
		loadspec = self.registerUIMethod(self.uiLoadImage, 'Load', argspec)
		self.registerUISpec(`self.id`, (watcherspec, loadspec))

	def uiLoadImage(self, filename):
		im = mrc_to_numeric(filename)
		self.displayNumericArray(im)
		return ''

if __name__ == '__main__':
	id = ('ImViewer',)
	i = ImViewer(id, {})
	signal.pause()
