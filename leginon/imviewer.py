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

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(target=self.open_viewer)
		self.viewerthread.setDaemon(1)
		self.viewerthread.start()
		print 'thread started'

	def publishClickInfo(self, event):
		clickinfo = self.iv.eventXYInfo(event)
		clickinfo['image id'] = self.imageid
		## prepare for xmlrpc
		c = {}
		for key,value in clickinfo.items():
			if value is not None:
				c[key] = value
		e = event.ClickImageEvent(self.ID(), c)
		self.outputEvent(e)

	def open_viewer(self):
		root = Tk()
		root.wm_maxsize(800,800)
		self.iv = ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.publishClickInfo)
		self.iv.pack()
		self.viewer_ready.set()
		root.mainloop()
		self.viewer_ready.clear()
		self.iv = None
	
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
