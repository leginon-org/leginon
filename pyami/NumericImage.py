#!/usr/bin/env python

from Tkinter import *
import Numeric
import Image
import ImageTk

## (Numeric typcode,size) => (PIL mode,  PIL rawmode)
ntype_itype = {
	(Numeric.UnsignedInt8,1) : ('L','L'),
	(Numeric.Int16,2) : ('I','I;16NS'),
	(Numeric.Int,2) : ('I','I;16NS'),
	(Numeric.Int,4) : ('I','I;32NS'),
	(Numeric.Int32,4) : ('I','I;32NS'),
	(Numeric.Float,4) : ('F','F;32NF'),
	(Numeric.Float,8) : ('F','F;64NF'),
	(Numeric.Float32,4) : ('F','F;32NF'),
	(Numeric.Float64,8) : ('F','F;64NF')
	}

def numeric_bin(ndata, bin):
	shape = ndata.shape
	if len(shape) != 2:
		raise RuntimeError, 'ndata must be 2-D Numeric array'
	if len(bin) != 2:
		raise RuntimeError, 'bin must be 2-tuple'
	if shape[0] % bin[0] or shape[1] % bin[1]:
		raise RuntimeError, 'shape must be multiple of bin'

	newshape = shape[0]/bin[0], shape[1]/bin[1]


class NumericImage(ImageTk.PhotoImage):
	"""extends the PIL PhotoImage to take 2D Numeric data, scaled to
	the clients preference"""

	def __init__(self,*args,**kargs):
		ImageTk.PhotoImage.__init__(self, *args, **kargs)

	def use_array(self, ndata):
		self.array = ndata
		self.array_min = min(Numeric.reshape(self.array,(1,-1))[0])
		self.array_max = max(Numeric.reshape(self.array,(1,-1))[0])

	def zoom(self, *args, **kargs):
		ImageTk.PhotoImage._PhotoImage__photo.zoom(self,*args,**kargs)

	def paste(self, clip=None):
		"""Paste a Numeric array into photo image.
		'clip' specifies the min and max values of the array
		that should be scaled to the display (0-255)
		If no clip is specified, default is min and max of array"""
		newim = self.array_to_image(clip)
		ImageTk.PhotoImage.paste(self, newim)

	def array_to_image(self, clip=None):
		h,w = self.array.shape
		size = (w,h)
		if len(size) != 2:
			return None

		## if no clip specified, use min and max of array
		if clip:
			minval,maxval = clip
		else:
			minval = self.array_min
			maxval = self.array_max

		if minval == None:
			minval = self.array_min
		if maxval == None:
			maxval = self.array_max

		range = maxval - minval
		try:
			scl = 255.0 / range
			off = -255.0 * minval / range
		except ZeroDivisionError:
			scl = 0.0
			off = 0.0
		newdata = scl * self.array + off
		
		type = newdata.typecode()
		itemsize = newdata.itemsize()
		im_mode = ntype_itype[type,itemsize][0]
		im_rawmode = ntype_itype[type,itemsize][1]

		nstr = newdata.tostring()

		stride = 0
		orientation = 1

		im = Image.fromstring( im_mode, size, nstr, "raw",
			        im_rawmode, stride, orientation
				        )
		return im

if __name__ == '__main__':
	root = Tk()
	can = Canvas(width = 512, height = 512, bg='blue')
	can.pack()

	mode = 'I'
	size = (128,256)
	ndata = Numeric.arrayrange(256**2/2)
	ndata.shape = size

	numphoto1 = NumericImage(mode, size)
	numphoto1.use_array(ndata)
	numphoto1.paste((10000,30000))

	numphoto2 = NumericImage(mode, size)
	numphoto2.use_array(ndata)
	numphoto2.paste()

	numphoto3 = NumericImage(mode, size)
	numphoto3.use_array(ndata)
	numphoto3.paste()

	numphoto4 = NumericImage(mode, size)
	numphoto4.use_array(ndata)
	numphoto4.paste()

	can.create_image(0,0,anchor=NW,image=numphoto1)
	can.create_image(0,256,anchor=NW,image=numphoto2)
	can.create_image(256,0,anchor=NW,image=numphoto3)
	can.create_image(256,256,anchor=NW,image=numphoto4)

	root.mainloop()
