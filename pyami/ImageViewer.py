#!/usr/bin/env python

import sys
from Tkinter import *
from ScrolledCanvas import *
from Mrc import *
from NumericImage import *

## wrapper around canvas image item and its associated PIL photo image
class ImageItem:
	def __init__(self, canvas, nwx, nwy):
		self.canvas = canvas
		realcanvas = canvas.canvas
		self.nwx = nwx
		self.nwy = nwy
		self.width = self.height = 0
		self.dispwidth = self.dispheight = 0
		self.zoomfactor = 1
		self.photoimage = NumericImage('L', (0,0))
		self.id = realcanvas.create_image(self.nwx, self.nwy, anchor=NW, image=self.photoimage)

	def create_clipper(self, parent):
		self.clippingwidget = ClippingWidget(parent, self)
		return self.clippingwidget

	def zoom(self):
		pass

	def show(self, clip=None):
		"""show the data with specified clipping tuple"""
		self.photoimage.paste(clip)

	def imagexy(self,canvasx,canvasy):
		"""return the image coords given the canvas coords"""

		if self.width == 0 or self.height == 0:
			return None

		imgx = int(canvasx - self.nwx)
		imgy = int(canvasy - self.nwy)
		zoomimgx = int( round( float(imgx) / self.zoomfactor) )
		zoomimgy = int( round( float(imgy) / self.zoomfactor) )

		### return None if out of bounds
		if imgx < 0 or imgx >= self.dispwidth:
			return None
		if imgy < 0 or imgy >= self.dispheight:
			return None

		return zoomimgx,zoomimgy

	def grey_level(self,x,y):
		"""returns the displayed grey level at pixel x,y"""
		return self.photoimage.get(x,y)

	def data_level(self,x,y):
		"""returns the value of the underlying data at pixel x,y"""
		### remember: Numeric array is transpose of image
		return self.photoimage.array[y][x]

	def import_numeric(self, data):
		"""
		import_numeric(image_id, data)
		puts data into image
		"""
		if len(data.shape) != 2:
			raise ValueError, "2D Numeric array required"
		self.height,self.width = data.shape
		## not taking into account zoom
		self.dispheight,self.dispwidth = data.shape

		self.photoimage.use_array(data)
		self.clippingwidget.update_extrema()
		self.show()
		self.canvas.fit_images()


class ImageCanvas(ScrolledCanvas):
	"""
	This is a ScrolledCanvas with special event bindings and
	easy management of any number of PhotoImage items
	"""
	def __init__(self,*args,**kargs):
		ScrolledCanvas.__init__(self,*args,**kargs)
		self['cursor'] = 'crosshair'
		self.images = []
		self.cursorinfo = CursorInfo(self)

		### linkable Tk variables
		self.can_x = IntVar()
		self.can_y = IntVar()
		self.img_x = IntVar()
		self.img_y = IntVar()
		self.img_i = IntVar()

	def new_image(self, x, y):
		"""
		Creates a new image on the canvas with NW corner at x,y.
		"""
		im = ImageItem(self, x, y)
		self.images.append( im )
		return im

	def leave_callback(self, event):
		ScrolledCanvas.leave_callback(self,event)
		self.canvas.delete('overlaytext')

	def motion_callback(self,event):
		ScrolledCanvas.motion_callback(self,event)
		can = self.canvas

		view_width = can.winfo_width()
		view_height = can.winfo_height()
		can_x = can.canvasx(event.x)
		can_y = can.canvasy(event.y)

		self.can_x.set(can_x)
		self.can_y.set(can_y)

		info = self.cursorinfo.query(can_x, can_y)

	def fit_images(self):
		"""resize the canvas to fit all its images"""
		### find the min/max extents of all images
		xmin = ymin = sys.maxint
		xmax = ymax = -sys.maxint
		for image in self.images:
			imgxmin = image.nwx
			imgymin = image.nwy
			imgxmax = imgxmin + image.dispwidth
			imgymax = imgymin + image.dispheight
			
			if imgxmin < xmin:
				xmin = imgxmin
			if imgxmax > xmax:
				xmax = imgxmax
			if imgymin < ymin:
				ymin = imgymin
			if imgymax > ymax:
				ymax = imgymax

		self.resize(xmin,ymin,xmax,ymax)


class CursorInfo:
	"""
	CursorInfo(imagecanvas)
	Maintains info about what is under the cursor.
	"""
	def __init__(self, imagecanvas):
		self.imagecanvas = imagecanvas
		self.imageitem = None
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
		for im in self.imagecanvas.images:
			imcoord = im.imagexy(canvasx, canvasy)
			if imcoord:
				img = im
				img_x = imcoord[0]
				img_y = imcoord[1]
				img_i = im.data_level(img_x,img_y)
				break

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
		self.xlab.pack(side=LEFT)
		self.ylab.pack(side=LEFT)
		self.ilab.pack(side=LEFT)


class ClippingWidget(Frame):
	def __init__(self, parent, imageitem, *args, **kargs):
		Frame.__init__(self, *args, **kargs)
		self.imageitem = imageitem
		self.clipmin = DoubleVar()
		self.clipmax = DoubleVar()
		self._build()

	def _build(self):
		self.minscale = Scale(self, variable=self.clipmin, orient=HORIZONTAL, command=self.clip, showvalue=NO, width=8, length=300)
		self.maxscale = Scale(self, variable=self.clipmax, orient=HORIZONTAL, command=self.clip, showvalue=NO, width=8, length=300)
		self.minlab = Label(self, textvariable=self.clipmin)
		self.maxlab = Label(self, textvariable=self.clipmax)

		self.minscale.grid(column=0, row=0)
		self.maxscale.grid(column=0, row=1)
		self.minlab.grid(column=1, row=0)
		self.maxlab.grid(column=1, row=1)

	def update_extrema(self):
		array_min = self.imageitem.photoimage.array_min
		array_max = self.imageitem.photoimage.array_max
		self.minscale['from_'] = array_min
		self.maxscale['from_'] = array_min
		self.minscale['to'] = array_max
		self.maxscale['to'] = array_max
		self.set(array_min, array_max)

	def set(self, newmin, newmax):
		self.clipmin.set(newmin)
		self.clipmax.set(newmax)

	def clip(self,newval=None):
		"""update the clipping on the imageitem"""
		newclip = (self.clipmin.get(), self.clipmax.get())
		self.imageitem.show(newclip)


class ImageViewer(Frame):
	"""
	May be initialized with options for the ImageViewer Frame.
	Methods:
		import_numeric(data):
		data is a 2D Numeric array that should be displayed 
		in the ImageViewer
	"""

	def __init__(self, *args, **kargs):
		Frame.__init__(self, *args, **kargs)
		self._build()

	## put together component widgets
	def _build(self):
		self.canvas = ImageCanvas(self, bg = '#acf',bd=4, relief=RAISED)
		self.canvas.pack(padx=4,pady=4,expand=YES,fill=BOTH,side=TOP)
		self.im = self.canvas.new_image(0,0)
		self.cursorinfo = CursorInfoWidget(self, self.canvas.cursorinfo)
		self.cursorinfo.pack(side=TOP)
		self.clipper = self.im.create_clipper(self)
		self.clipper.pack(side=TOP)

	def info_bar(self, state):
		if state == ON:
			pass
		elif state == OFF:
			pass

	def import_numeric(self, data):
		"""
		import_numeric(numarray, clip)
		Display 2D Numeric array in this ImageViewer.
		Optional 'clip' tuple gives min and max value to display
		"""
		self.im.import_numeric(data)
		h,w = data.shape
		self.canvas.resize(0,0,w,h)

	def show(self, clip=None):
		self.im.show(clip)

	## resize my canvas when I am resized
	def configure_callback(self, event):
		self.canvas['width'] = event.width
		self.canvas['height'] = event.height

if __name__ == '__main__':
	root = Tk()

	jim = ImageViewer(root, bg='#488')
	jim.pack()



	## read mrc image into Numeric array
	data1 = mrc_to_numeric('test1.mrc')
	data1 = data1[:256]

	#import Numeric
	#data = Numeric.arrayrange(16384)
	#data.shape = (128,128)

	## create a photo image and plug it into the viewer
	jim.import_numeric(data1)

	root.mainloop()
