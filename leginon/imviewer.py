#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
from viewer.ImageViewer import ImageViewer
import watcher

import node, event

class ImViewer(watcher.Watcher):
	def __init__(self, id, managerlocation):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, managerlocation, watchfor, lockblocking)
		t = threading.Thread(target=self.open_viewer)
		t.setDaemon(1)
		t.start()

	def open_viewer(self):
		root = Tk()
		root.wm_maxsize(800,800)
		self.iv = ImageViewer(root, bg='#488')
		self.iv.pack()
		root.mainloop()
	
	def processData(self, imagedata):
		#camdict = imagedata.content
		#imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		#width = camdict['x dimension']
		#height = camdict['y dimension']
		#numarray = Numeric.array(imarray)
		#numarray.shape = (height,width)

		## self.im must be 2-d numeric data

		numarray = imagedata.content
		self.iv.import_numeric(numarray)
		self.iv.update()
