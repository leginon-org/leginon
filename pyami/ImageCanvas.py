#!/usr/bin/env python

from Tkinter import *

from NumericImage import *
from ImageTk import *


class ImageCanvas(Canvas):
	"""
	ImageCanvas is a Canvas with a NumericImage
	"""
	def __init__(self, *args, **kargs):
		Canvas.__init__(self, *args, **kargs)
		self.canimage = self.create_image(0, 0, anchor=NW)
		self.numimage = None
		self.zoomfactor = 1.0

	def use_numeric(self, ndata):
		self.numimage = NumericImage(ndata)

	def image_display(self, disprange=(None,None)):
		self.numimage.transform['clip'] = disprange
		self.numimage.update_image()
		self.photo = self.numimage.photoimage()
		newwidth = self.photo.width()
		newheight = self.photo.height()
		self.resize(0,0,newwidth,newheight)
		self.itemconfig(self.canimage, image=self.photo)
		self.update()

	def data_level(self, x, y):
		return self.numimage.get(x,y)

	def resize(self, x1, y1, x2, y2):
		newwidth = x2 - x1
		newheight = y2 - y1
		self['width'] = newwidth
		self['height'] = newheight
		self['scrollregion'] = (x1,y1,x2,y2)

	def imagexy(self, canvasx, canvasy):
		"""return the image coords given the canvas coords"""
		if self['width'] == 0 or self['height'] == 0:
			return None

		zoomimgx = int( round( float(canvasx) / self.zoomfactor) )
		zoomimgy = int( round( float(canvasy) / self.zoomfactor) )

		return zoomimgx,zoomimgy

if __name__ == '__main__':
	from Mrc import *
	root = Tk()
	root.positionfrom('user')

	ic = ImageCanvas(root, bg='blue')
	ic.pack()

	imdata = mrc_to_numeric('test1.mrc')
	ic.use_numeric(imdata)
	ic.numimage['clip'] = (None,None)
	ic.image_display()

	root.mainloop()
