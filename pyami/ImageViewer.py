#!/usr/bin/env python

from Tkinter import *
from ImageCanvas import *
#from NumericImage import *


class ImageViewer(Frame):
	"""
	May be initialized with options for the ImageViewer Frame.
	Methods:
		import_numeric(data):
		data is a 2D Numeric array that should be displayed 
		in the ImageViewer
	"""

	def __init__(self, parent, *args, **kargs):
		Frame.__init__(self, parent, *args, **kargs)
		self._build()

	## put together component widgets
	def _build(self):
		self.canvas = ImageCanvas(self, bg = '#acf',bd=4, relief=RAISED)
		self.cursorinfowid = self.canvas.cursorinfo_widget(self, bg='#acf')
		#self.canvas.bind('<Configure>', self.configure_callback)

		self.scaler = ScalingWidget(self)
		self.scaler.add_imagecanvas(self.canvas)

		self.zoomframe = Frame(self)
		Button(self.zoomframe, text='Zoom In', command=self.zoomin).pack()
		Button(self.zoomframe, text='Zoom Out', command=self.zoomout).pack()

		self.cursorinfowid.pack(side=TOP)
		self.scaler.pack(side=BOTTOM)
		self.zoomframe.pack(side=BOTTOM)
		self.canvas.pack(padx=4,pady=4,expand=YES,fill=BOTH,side=TOP)

	def import_numeric(self, data):
		"""
		import_numeric(numarray)
		Display 2D Numeric array in this ImageViewer.
		Optional 'clip' tuple gives min and max value to display
		"""
		self.canvas.use_numeric(data)

	def clip(self, newclip=None):
		return self.canvas.clip(newclip)

	def zoomin(self):
		self.canvas.zoom(2)
	def zoomout(self):
		self.canvas.zoom(0.5)


if __name__ == '__main__':
	import sys
	filename = sys.argv[1]
	root = Tk()

	print 'create ImageViewer'
	jim = ImageViewer(root, bg='#488')
	print 'pack ImageViewer'
	jim.pack()

	print 'read MRC'
	from mrc import Mrc
	data1 = Mrc.mrc_to_numeric(filename)

	print 'data into ImageViewer'
	while 1:
		jim.import_numeric(data1)
		raw_input('return to continue')
	#print 'clip ImageViewer'
	#jim.clip((500,700))
	#print 'mainloop'
	#root.mainloop()
