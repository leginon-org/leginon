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
	jim = TestClickable(root, bg='#acf')
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
