#!/usr/bin/env python

import watcher
import correlator
import data, event
from mrc.Mrc import mrc_to_numeric
from Tkinter import *
from viewer.ImageViewer import ImageViewer
import threading

class ShiftMeter(watcher.Watcher):
	'''
	This node watches for published images.  It inserts images into
	its buffer, which can hold two images.  The shift between the two
	images in the buffer is measured after every insert.
	'''
	def __init__(self, id, managerlocation):
		watchfor = event.ImagePublishEvent
		lockblocking = 0
		watcher.Watcher.__init__(self, id, managerlocation, watchfor, lockblocking)
		self.correlator = correlator.Correlator(1)

		#t = threading.Thread(target=self.initViewers)
		#t.setDaemon(1)
		#t.start()

	def processData(self, newdata):
		shiftinfo = self.correlator.insert(newdata)
		if shiftinfo == {}: return

		# prepare shiftinfo for publishing
		if shiftinfo.has_key('cross correlation image'):
			ccid = self.ID()
			cc = shiftinfo['cross correlation image']
			ccdata = data.CrossCorrelationImageData(ccid, cc)
			self.publish(ccdata, eventclass=event.CrossCorrelationImagePublishEvent)
			ccshift = shiftinfo['cross correlation shift']
			# publish only the id of the image
			shiftinfo['cross correlation image'] = ccid

		if shiftinfo.has_key('phase correlation image'):
			pcid = self.ID()
			pc = shiftinfo['phase correlation image']
			pcdata = data.PhaseCorrelationImageData(pcid, pc)
			self.publish(pcdata, eventclass=event.PhaseCorrelationImagePublishEvent)
			pcshift = shiftinfo['phase correlation shift']
			# publish only the id of the image
			shiftinfo['phase correlation image'] = pcid
		print '****IMAGE PUBLISHED'
		print 'shiftinfo', shiftinfo
		corrdata = data.CorrelationData(self.ID(), shiftinfo)
		self.publish(corrdata, eventclass=event.CorrelationPublishEvent)

	def process_numeric(self, numarray):
		'''mainly for debugging'''
		class fakedata: pass
		fakedata.content = numarray
		fakedata.id = (filename,)
		print 'processing data'
		self.processData(fakedata)

	def defineUserInterface(self):
		watcher.Watcher.defineUserInterface(self)
		argspec = (
			{'name':'filename', 'alias':'Filename', 'type':'string'},
			)
		self.registerUIFunction(self.uiLoadImage, argspec, 'Load')
		self.registerUIFunction(self.uiClearBuffer, (), 'Clear Buffer')

	def uiLoadImage(self, filename):
		print 'reading %s' % filename
		newimage = mrc_to_numeric(filename)
		print 'image read'
		self.process_numeric(newimage)
		return 'image loaded'

	def uiClearBuffer(self):
		self.correlator.clear()
		return ''

	def initViewers(self):
		ccwin = Toplevel()
		ccwin.wm_title('Cross Correlation')
		self.cciv = ImageViewer(ccwin)

		pcwin = Toplevel()
		pcwin.wm_title('Phase Correlation')
		self.pciv = ImageViewer(pcwin)

		self.cciv.pack()
		self.pciv.pack()
		ccwin.mainloop()

	def updateViewers(self, ccim, pcim):
		self.cciv.import_numeric(ccim)
		self.pciv.import_numeric(pcim)


if __name__ == '__main__':
	from Tkinter import *
	import nodegui

	s = ShiftMeter(('none',), None)

	host = s.location()['hostname']
	uiport = s.location()['UI port']
	
	tk = Tk()
	sgui = nodegui.NodeGUI(tk, hostname=host, port=uiport)
	sgui.pack()
	tk.mainloop()
