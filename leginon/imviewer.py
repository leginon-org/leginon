#!/usr/bin/env python

from Tkinter import *
import array, base64
import threading
import Numeric
from viewer.ImageViewer import ImageViewer

import node, event

class ImViewer(node.Node):
	def __init__(self, nodeid, managerlocation):
		node.Node.__init__(self, nodeid, managerlocation)

		self.addEventInput(event.PublishEvent, self.handle_publish)

		self.open_viewer()
		self.lock = threading.RLock()


	def handle_publish(self, pubevent):
		### drop any events while another is being processed
		if not self.lock.acquire(blocking=0):
			print 'dropping event %s' % pubevent
			return

		dataid = pubevent.content
		print 'received publish event %s with dataid %s' % (publishevent, dataid)

		self.im = researchByDataID(dataid)
		self.display_image()

		self.lock.release()

	def open_viewer(self):
		root = Tk()
		self.iv = ImageViewer(root, bg='#488')
		self.iv.pack()
		root.mainloop()
	
	def display_image(self):
		camdict = self.im.content
		imarray = array.array(camdict['datatype code'], base64.decodestring(camdict['image data']))
		
		width = camdict['x dimension']
		height = camdict['y dimension']

		numarray = Numeric.array(imarray)
		numarray.shape = (height,width)

		## self.im must be 2-d numeric data
		self.iv.import_numeric(numarray)


if __name__ == '__main__':
	import signal, sys

	manloc = {}
	manloc['hostname'] = sys.argv[1]
	manloc['TCP port'] = int(sys.argv[2])

	m = MyNode(None, manloc)
	try:
		signal.pause()
	except KeyboardInterrupt:
		sys.exit()
