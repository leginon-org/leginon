#!/usr/bin/env python

from Tkinter import *
from ScrolledCanvas import *
from Mrc import *
from NumericImage import *

## wrapper around canvas image item and its associated PIL photo image
class ImageItem:
	def __init__(self, canvas, nwx, nwy):
		self.photoimage = NumericImage('L', (0,0))
		self.nwx = nwx
		self.nwy = nwy
		self.id = canvas.create_image(self.nwx, self.nwy, anchor=NW, image=self.photoimage)
		self.width = -1
		self.height = -1

	def imagexy(self,canvasx,canvasy):
		"""
		return the image coords given the canvas coords
		"""
		x = int(canvasx - self.nwx)
		y = int(canvasy - self.nwy)

		### return None if out of bounds
		if x < 0 or x >= self.width:
			return None
		if y < 0 or y >= self.height:
			return None
		return x,y

	def grey_level(self,x,y):
		"""returns the displayed grey level at pixel x,y"""
		return self.photoimage.get(x,y)

	def data_level(self,x,y):
		"""returns the value of the underlying data at pixel x,y"""
		return self.photoimage.array[y][x]

	def import_numeric(self, data):
		"""
		import_numeric(image_id, data)
		puts data into image
		"""
		if len(data.shape) != 2:
			raise ValueError, "2D Numeric array required"
		self.height,self.width = data.shape

		self.photoimage.use_array(data)
		self.photoimage.paste_array()


class ImageCanvas(ScrolledCanvas):
	"""
	This is a ScrolledCanvas with special event bindings and
	easy management of any number of PhotoImage items
	"""
	def __init__(self,*args,**kargs):
		ScrolledCanvas.__init__(self,*args,**kargs)
		self.images = []

		### linkable Tk variables
		self.can_x = IntVar()
		self.can_y = IntVar()
		self.img_x = IntVar()
		self.img_y = IntVar()
		self.img_i = IntVar()

	def create_image_item(self, x, y):
		"""
		Creates a new image on the canvas with NW corner at x,y.
		"""
		im = ImageItem(self.canvas, x, y)
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

		### find an image, if any, that is below the cursor
		### may not be the top image if overlapping!!!
		for im in self.images:
			imcoord = im.imagexy(can_x, can_y)
			print 'imcoord', imcoord
			if imcoord:
				img = im
				img_x = imcoord[0]
				img_y = imcoord[1]
				img_i = im.data_level(img_x,img_y)
				break
			else:
				img_x = None
				img_y = None
				img_i = None

			self.img_x.set(img_x)
			self.img_y.set(img_y)
			self.img_i.set(img_i)


class PixelDataBar(Frame):
	def __init__(self, *args, **kargs):
		Frame.__init__(self, *args, **kargs)
		

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
		self['bg'] = 'red'
		self._build()

	## put together component widgets
	def _build(self):
		self.heading = Label(self, text='ImageViewer')
		self.heading.pack(side=TOP, padx=3,pady=3)

		self.canvas = ImageCanvas(self, bg = 'blue',bd=4, relief=RAISED)
		self.canvas.pack(padx=3,pady=3,expand=YES,fill=BOTH,side=TOP)
		self.im = self.canvas.create_image_item(0,0)

	def info_bar(self, state):
		if state == ON:
			pass
		elif state == OFF:
			pass

	def import_numeric(self, data):
		self.im.import_numeric(data)
		h,w = data.shape
		self.canvas.resize(w,h)

	## resize my canvas when I am resized
	def configure_callback(self, event):
		self.canvas['width'] = event.width
		self.canvas['height'] = event.height
		#print 'event:', event
		#print dir(event)

if __name__ == '__main__':
	root = Tk()

	jim = ImageViewer(root)
	jim.pack()

	## read mrc image into Numeric array
	data = mrc_to_numeric('test1.mrc')
	data = data[:256]

	#import Numeric
	#data = Numeric.arrayrange(16384)
	#data = Numeric.reshape(data, (128,128))

	## create a photo image and plug it into the viewer
	jim.import_numeric(data)

	root.mainloop()
