#!/usr/bin/env python

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
		self._build()

	## put together component widgets
	def _build(self):
		self.canvas = ImageCanvas(self, bg = '#acf',bd=4, relief=RAISED)
		self.cursorinfowid = self.canvas.cursorinfo_widget(self, bg='#acf')
		#self.canvas.bind('<Configure>', self.configure_callback)

		self.scaler = self.canvas.scaling_widget(self)

		self.zoomframe = Frame(self)
		Button(self.zoomframe, text='Zoom In', command=self.zoomin).pack(side=LEFT)
		Button(self.zoomframe, text='Zoom Out', command=self.zoomout).pack(side=LEFT)

		self.cursorinfowid.pack(side=TOP)
		self.scaler.pack(side=TOP)
		self.zoomframe.pack(side=TOP)
		self.canvas.pack(padx=4,pady=4,expand=YES,fill=BOTH,side=BOTTOM)

		self.update()

	def import_numeric(self, data):
		"""
		import_numeric(numarray)
		Display 2D Numeric array in this ImageViewer.
		Optional 'clip' tuple gives min and max value to display
		"""
		self.imagearray = data
		self.canvas.use_numeric(data)

	def displayMessage(self, message):
		self.canvas.displayMessage(message)

	def clip(self, newclip=None):
		return self.canvas.clip(newclip)

	def zoomin(self):
		self.canvas.zoom(2)
	def zoomout(self):
		self.canvas.zoom(0.5)

	def bindCanvas(self, event, func):
		self.canvas.bindCanvas(event, func)

	def eventXYInfo(self, event):
		return self.canvas.eventXYInfo(event)


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
	jim = TestClickable(root, bg='#488')
	#jim = ImageViewer(root, bg='#488')
	jim.pack()
	
	#for filename in sys.argv[1:]:
	#	data1 = Mrc.mrc_to_numeric(filename)
	#	jim.import_numeric(data1)
	#	raw_input('return to continue')

	screenw = root.winfo_reqwidth()
	screenh = root.winfo_reqheight()
	print 'wh', screenw, screenh

	filename = sys.argv[1]
	data1 = Mrc.mrc_to_numeric(filename)
	jim.import_numeric(data1)

	screenw = root.winfo_width()
	screenh = root.winfo_height()
	print 'wh', screenw, screenh

	root.mainloop()
	
	#print 'clip ImageViewer'
	#jim.clip((500,700))
	#print 'mainloop'
	#root.mainloop()
