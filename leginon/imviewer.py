#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
import signal, time

from ImageViewer import ImageViewer
import watcher
import node, event, data
from Mrc import mrc_to_numeric
import cameraimage


class ImViewer(watcher.Watcher):
	def __init__(self, id, nodelocations):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, nodelocations, watchfor, lockblocking)

		self.addEventOutput(event.ImageClickEvent)

		self.iv = None
		self.viewer_ready = threading.Event()
		self.start_viewer_thread()

	def die(self, killevent):
		self.close_viewer()
		self.exit()

	def start_viewer_thread(self):
		if self.iv is not None:
			return
		self.viewerthread = threading.Thread(target=self.open_viewer)
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

		#print 'acqbut'
		buttons = Frame(root)
		self.acqbut = Button(buttons, text='Acquire', command=self.acquire)
		self.acqbut.pack(side=LEFT)
		self.acqeventbut = Button(buttons, text='Acquire Event', command=self.acquireEvent)
		self.acqeventbut.pack(side=LEFT)
		buttons.pack(side=TOP)

		#print 'iv'
		self.iv = ImageViewer(root, bg='#488')
		self.iv.bindCanvas('<Double-1>', self.clickEvent)
		#print 'iv pack'
		self.iv.pack()

		#print 'viewer_ready.set'
		self.viewer_ready.set()
		#print 'mainloop'
		root.mainloop()

		##clean up if window destroyed
		self.viewer_ready.clear()
		self.iv = None

	def close_viewer(self):
		try:
			self.root.destroy()
		except TclError:
			pass

	def acquire(self):
		### Camera State Data Spec
		defaultsize = (512,512)
		camerasize = (2048,2048)
		offset = cameraimage.centerOffset(camerasize,defaultsize)
		camstate = {
			'exposure time': 500,
			'binning': {'x':1, 'y':1},
			'dimension': {'x':defaultsize[0], 'y':defaultsize[1]},
			'offset': {'x': offset[0], 'y': offset[1]}
		}
		camdata = data.EMData('camera', camstate)
		print 'publishing camdata'
		self.publishRemote(camdata)

		self.acqbut['state'] = DISABLED
		print 'researching image data'
		imdata = self.researchByDataID('image data')
		print 'displaying'
		self.displayNumericArray(imdata.content['image data'])
		print 'done'
		self.acqbut['state'] = NORMAL

	def acquireEvent(self):
		self.acqeventbut['state'] = DISABLED
		#print 'sending ImageAcquireEvent'
		e = event.ImageAcquireEvent(self.ID())
		#print 'e', e
		self.outputEvent(e)
		#print 'sent ImageAcquireEvent'
		self.acqeventbut['state'] = NORMAL
	
	def processData(self, imagedata):
		#camdict = imagedata.content
		#imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		#width = camdict['x dimension']
		#height = camdict['y dimension']
		#numarray = Numeric.array(imarray)
		#numarray.shape = (height,width)

		## self.im must be 2-d numeric data

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
