#!/usr/bin/env python

import sys
from Tkinter import *
from ScrolledCanvas import *
import Mrc
from NumericImage import *


class CursorInfo:
	"""
	CursorInfo(imagecanvas)
	Maintains info about what is under the cursor.
	"""
	def __init__(self, imagecanvas):
		self.imagecanvas = imagecanvas
		self.imagex = IntVar()
		self.imagey = IntVar()
		self.imagedata = DoubleVar()
		self.imagelevel = IntVar()

	def query(self, canvasx, canvasy):
		"""
		find an image, if any, that is below the cursor
		This may not be the top image if overlapping!!!
		"""
		img = None
		img_x = None
		img_y = None
		img_i = None
		im = self.imagecanvas.canvas
		imcoord = im.imagexy(canvasx, canvasy)
		if imcoord:
			img = im
			img_x = imcoord[0]
			img_y = imcoord[1]
			img_i = im.data_level(img_x,img_y)

		self.imageitem = img
		self.imagex.set(img_x)
		self.imagey.set(img_y)
		self.imagedata.set(img_i)

		return (img, img_x, img_y, img_i)
		
class CursorInfoWidget(Frame):
	def __init__(self, parent, cursorinfo, *args, **kargs):
		Frame.__init__(self, *args, **kargs)
		self.xlab = Label(self, textvariable=cursorinfo.imagex, width=6)
		self.ylab = Label(self, textvariable=cursorinfo.imagey, width=6)
		self.ilab = Label(self, textvariable=cursorinfo.imagedata, width=6)
		self['bg'] = parent['bg']
		self.xlab['bg'] = parent['bg']
		self.ylab['bg'] = parent['bg']
		self.ilab['bg'] = parent['bg']
		self.xlab.pack(side=LEFT)
		self.ylab.pack(side=LEFT)
		self.ilab.pack(side=LEFT)


class ScalingWidget(Frame):
	def __init__(self, parent, *args, **kargs):
		Frame.__init__(self, parent, *args, **kargs)
		self.imageviewer = parent
		self.numimage = None
		self.rangemin = DoubleVar()
		self.rangemax = DoubleVar()
		self._build()

	def _build(self):
		self.minscale = Scale(self, variable=self.rangemin, orient=HORIZONTAL, command=self.update_image, showvalue=NO, width=8, length=300)
		self.maxscale = Scale(self, variable=self.rangemax, orient=HORIZONTAL, command=self.update_image, showvalue=NO, width=8, length=300)
		self.minlab = Label(self, textvariable=self.rangemin)
		self.maxlab = Label(self, textvariable=self.rangemax)

		self.minscale.grid(column=0, row=0)
		self.maxscale.grid(column=0, row=1)
		self.minlab.grid(column=1, row=0)
		self.maxlab.grid(column=1, row=1)

	def update_extrema(self):
		#array_min = self.imageitem.photoimage.array_min
		#array_max = self.imageitem.photoimage.array_max
		array_min,array_max = self.numimage.extrema
		self.minscale['from_'] = array_min
		self.maxscale['from_'] = array_min
		self.minscale['to'] = array_max
		self.maxscale['to'] = array_max
		self.set(array_min, array_max)

	def set(self, newmin, newmax):
		self.rangemin.set(newmin)
		self.rangemax.set(newmax)

	def use_image(self, image):
		self.numimage = image
		self.update_extrema()

	def update_image(self,newval=None):
		"""update the clipping on the imageitem"""
		newrange = (self.rangemin.get(), self.rangemax.get())
		self.imageviewer.show(newrange)


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
		self.canvas = ScrolledCanvas(self, bg = '#acf',bd=4, relief=RAISED)
		self.cursorinfo = CursorInfo(self.canvas)
		self.cursorinfowid = CursorInfoWidget(self, self.cursorinfo,bg='#acf')
		self.canvas.canvas.bind('<Motion>', self.motion_callback)

		self.scaler = ScalingWidget(self)

		self.cursorinfowid.pack(side=TOP)
		self.scaler.pack(side=BOTTOM)
		self.canvas.pack(padx=4,pady=4,expand=YES,fill=BOTH,side=TOP)

	def import_numeric(self, data):
		"""
		import_numeric(numarray)
		Display 2D Numeric array in this ImageViewer.
		Optional 'clip' tuple gives min and max value to display
		"""
		self.canvas.canvas.use_numeric(data)
		self.scaler.use_image(self.canvas.canvas.numimage)

	def show(self, range=(None,None)):
		self.canvas.canvas.image_display(range)

	def motion_callback(self, event):
		x = event.x
		y = event.y
		canx = self.canvas.canvas.canvasx(x)
		cany = self.canvas.canvas.canvasy(y)
		self.cursorinfo.query(canx,cany)

	## resize my canvas when I am resized
	def configure_callback(self, event):
		self.canvas.canvas.resize(0,0,event.width, event.height)


if __name__ == '__main__':
	root = Tk()

	jim = ImageViewer(root, bg='#488')
	jim.pack()

	data1 = Mrc.mrc_to_numeric('test1.mrc')

	jim.import_numeric(data1)
	jim.show()

	root.mainloop()
