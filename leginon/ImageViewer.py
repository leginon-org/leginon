#!/usr/bin/env python

#
# COPYRIGHT:
#       The Leginon software is Copyright 2003
#       The Scripps Research Institute, La Jolla, CA
#       For terms of the license agreement
#       see  http://ami.scripps.edu/software/leginon-license
#

from Tkinter import *
from ImageCanvas import ImageCanvas, ScalingWidget

class ImageViewer(Frame):
	"""
	May be initialized with options for the ImageViewer Frame.
	Methods:
		import_numeric(data):
		data is a 2D Numeric array that should be displayed 
		in the ImageViewer
	"""

	def __init__(self, parent, **kwargs):
		Frame.__init__(self, parent, **kwargs)
		self.imagearray = None
		self._build()

	## put together component widgets
	def _build(self):
		self.canvas = ImageCanvas(self, bg=self['bg'],bd=4, relief=RAISED)
		#self.canvas.bind('<Configure>', self.configure_callback)

		self.scaler = self.canvas.scaling_widget(self)
		zframe = Frame(self, bg=self['bg'])
		self.cursorinfowid = self.canvas.cursorinfo_widget(zframe)
		self.zoomer = self.canvas.zooming_widget(zframe)
		self.cross = self.canvas.crosshairs_widget(zframe)

		#tarframe = Toplevel(self)
		#self.targets = self.canvas.targets_widget(tarframe)
		#self.targets.pack()

		self.cross.pack(side=LEFT)
		self.cursorinfowid.pack(side=LEFT)
		self.zoomer.pack(side=LEFT)

		self.scaler.pack(side=TOP)
		zframe.pack(side=TOP)
		self.canvas.pack(padx=4,pady=4,expand=YES,fill=BOTH,side=BOTTOM)

		self.update()

	def import_numeric(self, data):
		"""
		import_numeric(numarray)
		Display 2D Numeric array in this ImageViewer.
		Optional 'clip' tuple gives min and max value to display
		"""
		if data is self.imagearray:
			return
		self.imagearray = data
		self.canvas.use_numeric(data)

	def displayMessage(self, message):
		self.canvas.displayMessage(message)

	def clip(self, newclip=None):
		return self.canvas.clip(newclip)

	def bindCanvas(self, event, func):
		self.canvas.bindCanvas(event, func)

	def eventXYInfo(self, event):
		return self.canvas.eventXYInfo(event)

	def targetClickerOn(self):
		self.canvas.targetClickerOn()

	def targetClickerOff(self):
		self.canvas.targetClickerOff()


class TestClickable(ImageViewer):
	def __init__(self, parent, **kwargs):
		ImageViewer.__init__(self, parent, **kwargs)
		self.bindCanvas('<1>', self.click_callback)

	def click_callback(self, event):
		info = self.eventXYInfo(event)
		print info


if __name__ == '__main__':
	import sys
	import Mrc

	root = Tk()
	screenh = root.winfo_screenheight()
	print 'screenh', screenh
	root.wm_maxsize(0,0)
	jim = ImageViewer(root, bg='#acf')
	jim.targetClickerOn()
	#jim = ImageViewer(root, bg='#488')
	jim.pack()
	
	if 1:
		for filename in sys.argv[1:]:
			data1 = Mrc.mrc_to_numeric(filename)
			jim.import_numeric(data1)
			raw_input('return to continue')
			root.update()

	if 0:
		filename = sys.argv[1]
		data1 = Mrc.mrc_to_numeric(filename)
		jim.import_numeric(data1)

	#root.mainloop()
